#!python3

import time
import gpiod
import spidev
import logging
from PIL import Image, ImageDraw
from glob import glob

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('display.log')
    ]
)
logger = logging.getLogger(__name__)

# SPI Configuration
SPI_BUS = 1
SPI_DEVICE = 0        # First device on bus
SPI_SPEED = 10000000  # 40MHz for ILI9341

# GPIO Configuration - using device paths
DC_CHIP = "/dev/gpiochip2"
DC_OFFSET = 4          # Line GPIO
RST_CHIP = "/dev/gpiochip4"
RST_OFFSET = 5

# Display Settings
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

# Chunk size for SPI transfers (must be <= 4096 bytes)
CHUNK_SIZE = 4096

class ILI9341:
    def __init__(self):
        logger.info("Initializing ILI9341 display")
        
        # Initialize SPI
        try:
            logger.debug(f"Opening SPI device {SPI_BUS}.{SPI_DEVICE}")
            self.spi = spidev.SpiDev()
            self.spi.open(SPI_BUS, SPI_DEVICE)
            self.spi.max_speed_hz = SPI_SPEED
            self.spi.mode = 0b00
            self.spi.bits_per_word = 8
            logger.info(f"SPI initialized - Mode: {self.spi.mode}, Speed: {self.spi.max_speed_hz}Hz")
        except Exception as e:
            logger.error(f"SPI initialization failed: {str(e)}")
            raise
        
        # Initialize GPIO using modern API
        try:
            logger.debug(f"Requesting DC line on {DC_CHIP} offset {DC_OFFSET}")
            self.dc_request = gpiod.request_lines(
                DC_CHIP,
                consumer="ILI9341_DC",
                config={
                    DC_OFFSET: gpiod.LineSettings(
                        direction=gpiod.line.Direction.OUTPUT,
                        output_value=gpiod.line.Value.INACTIVE
                    )
                }
            )
            logger.debug(f"Requesting RST line on {RST_CHIP} offset {RST_OFFSET}")
            self.rst_request = gpiod.request_lines(
                RST_CHIP,
                consumer="ILI9341_RST",
                config={
                    RST_OFFSET: gpiod.LineSettings(
                        direction=gpiod.line.Direction.OUTPUT,
                        output_value=gpiod.line.Value.INACTIVE
                    )
                }
            )
            logger.info("GPIO successfully initialized")
        except Exception as e:
            logger.error(f"GPIO initialization failed: {str(e)}")
            self.spi.close()
            raise
        
        self.initialize()
    
    def initialize(self):
        """Initialize the display with hardware reset and commands"""
        logger.info("Starting display initialization")
        
        # Hardware reset
        logger.debug("Beginning hardware reset sequence")
        self.rst_request.set_value(RST_OFFSET, gpiod.line.Value.ACTIVE)  # High
        logger.debug("RST: HIGH (inactive)")
        time.sleep(0.005)
        
        self.rst_request.set_value(RST_OFFSET, gpiod.line.Value.INACTIVE)  # Low
        logger.debug("RST: LOW (active)")
        time.sleep(0.02)
        
        self.rst_request.set_value(RST_OFFSET, gpiod.line.Value.ACTIVE)  # High
        logger.debug("RST: HIGH (inactive)")
        time.sleep(0.15)
        logger.info("Hardware reset completed")
        
        # ILI9341 initialization sequence
        init_commands = [
            (0xEF, [0x03, 0x80, 0x02], "Software Reset"),
            (0xCF, [0x00, 0xC1, 0x30], "Power Control B"),
            # ... (keep all other commands from original)
            (0x29, None, "Display ON")
        ]
        
        # Send initialization commands with logging
        for cmd, data, desc in init_commands:
            logger.debug(f"Sending command: 0x{cmd:02X} ({desc})")
            self.command(cmd)
            if data:
                logger.debug(f"Command data: {[f'0x{x:02X}' for x in data]}")
                self.data(data)
        
        time.sleep(0.12)
        logger.info("Display initialization sequence completed")
    
    def command(self, cmd):
        """Send command to display (DC low)"""
        logger.debug(f"CMD: 0x{cmd:02X} (DC LOW)")
        self.dc_request.set_value(DC_OFFSET, gpiod.line.Value.INACTIVE)
        try:
            self.spi.xfer([cmd])
        except Exception as e:
            logger.error(f"Failed to send command 0x{cmd:02X}: {str(e)}")
            raise
    
    def data(self, data):
        """Send data to display (DC high)"""
        logger.debug(f"DATA: {len(data)} bytes (DC HIGH)")
        self.dc_request.set_value(DC_OFFSET, gpiod.line.Value.ACTIVE)
        
        if isinstance(data, list):
            # Log first 10 bytes to avoid flooding
            sample = data[:10]
            logger.debug(f"Data sample: {[f'0x{x:02X}' for x in sample]}{'...' if len(data) > 10 else ''}")
            
            # Split large data into chunks
            for i in range(0, len(data), CHUNK_SIZE):
                chunk = data[i:i+CHUNK_SIZE]
                try:
                    self.spi.xfer(chunk)
                except Exception as e:
                    logger.error(f"SPI transfer failed at chunk {i//CHUNK_SIZE}: {str(e)}")
                    raise
        else:
            try:
                self.spi.xfer([data])
            except Exception as e:
                logger.error(f"Failed to send data byte: {str(e)}")
                raise
    
    def set_window(self, x0, y0, x1, y1):
        """Set display window for drawing"""
        logger.debug(f"Setting window: X({x0}-{x1}), Y({y0}-{y1})")
        self.command(0x2A)  # Column Address Set
        self.data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
        self.command(0x2B)  # Page Address Set
        self.data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
        self.command(0x2C)  # Memory Write
    
    def fill_screen(self, color):
        """Fill screen with RGB565 color"""
        hi, lo = (color >> 8) & 0xFF, color & 0xFF
        logger.info(f"Filling screen with color 0x{hi:02X}{lo:02X}")
        
        self.set_window(0, 0, DISPLAY_WIDTH-1, DISPLAY_HEIGHT-1)
        self.dc_request.set_value(DC_OFFSET, gpiod.line.Value.ACTIVE)
        
        total_pixels = DISPLAY_WIDTH * DISPLAY_HEIGHT
        pixels_per_chunk = CHUNK_SIZE // 2
        buffer = bytearray([hi, lo])
        
        logger.debug(f"Total pixels: {total_pixels}, Chunk size: {pixels_per_chunk} pixels")
        
        for i in range(0, total_pixels, pixels_per_chunk):
            chunk_size = min(pixels_per_chunk, total_pixels - i)
            try:
                self.spi.writebytes(buffer * chunk_size)
            except Exception as e:
                logger.error(f"Fill failed at pixel {i}: {str(e)}")
                raise
            
            # Log progress every 10%
            if (i // pixels_per_chunk) % (total_pixels // (pixels_per_chunk * 10)) == 0:
                progress = (i / total_pixels) * 100
                logger.debug(f"Fill progress: {progress:.1f}%")
    
    def display_image(self, image):
        """Display PIL image"""
        logger.info("Starting image display")
        
        if image.mode != 'RGB':
            logger.debug("Converting image to RGB")
            image = image.convert('RGB')
            
        logger.debug("Converting to RGB565")
        rgb565_data = bytearray()
        for y in range(DISPLAY_HEIGHT):
            for x in range(DISPLAY_WIDTH):
                r, g, b = image.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                rgb565_data.append(rgb565 >> 8)
                rgb565_data.append(rgb565 & 0xFF)
        
        logger.debug(f"Image data size: {len(rgb565_data)} bytes")
        self.set_window(0, 0, DISPLAY_WIDTH-1, DISPLAY_HEIGHT-1)
        self.dc_request.set_value(DC_OFFSET, gpiod.line.Value.ACTIVE)
        
        # Send image data in chunks
        chunk_count = len(rgb565_data) // CHUNK_SIZE
        logger.debug(f"Sending {chunk_count + 1} chunks")
        
        for i in range(0, len(rgb565_data), CHUNK_SIZE):
            chunk = rgb565_data[i:i+CHUNK_SIZE]
            try:
                self.spi.writebytes(chunk)
            except Exception as e:
                logger.error(f"Image transfer failed at byte {i}: {str(e)}")
                raise
            
            # Log progress every 10%
            if (i // CHUNK_SIZE) % (chunk_count // 10) == 0:
                progress = (i / len(rgb565_data)) * 100
                logger.debug(f"Transfer progress: {progress:.1f}%")
        
        logger.info("Image display completed")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")
        try:
            self.spi.close()
            logger.debug("SPI closed")
        except Exception as e:
            logger.error(f"Error closing SPI: {str(e)}")
        
        try:
            self.dc_request.release()
            logger.debug("DC GPIO released")
        except Exception as e:
            logger.error(f"Error releasing DC GPIO: {str(e)}")
        
        try:
            self.rst_request.release()
            logger.debug("RST GPIO released")
        except Exception as e:
            logger.error(f"Error releasing RST GPIO: {str(e)}")

def create_test_image():
    """Create test image with colored rectangles"""
    img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Red rectangle
    draw.rectangle([(0, 0), (DISPLAY_WIDTH-1, DISPLAY_HEIGHT//3)], fill='red')
    
    # Green rectangle
    draw.rectangle([(0, DISPLAY_HEIGHT//3), (DISPLAY_WIDTH-1, 2*DISPLAY_HEIGHT//3)], fill='green')
    
    # Blue rectangle
    draw.rectangle([(0, 2*DISPLAY_HEIGHT//3), (DISPLAY_WIDTH-1, DISPLAY_HEIGHT-1)], fill='blue')
    
    # White text
    draw.text((80, 150), "ILI9341", fill='white')
    
    return img


if __name__ == "__main__":
    try:
        logger.info("Starting display test application")
        display = ILI9341()
        test_image = create_test_image()
        
        try:
            logger.info("Displaying test image")
            display.display_image(test_image)
            time.sleep(3)
            
            logger.info("Starting color cycle test")
            colors = [
                0xF800,  # Red
                0x07E0,  # Green
                0x001F,  # Blue
                0xFFFF,  # White
                0x0000   # Black
            ]
            
            while True:
                for color in colors:
                    logger.debug(f"Displaying color 0x{color:04X}")
                    display.fill_screen(color)
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.critical(f"Application error: {str(e)}", exc_info=True)
        finally:
            display.cleanup()
            logger.info("Application shutdown complete")
    
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}", exc_info=True)
        raise
