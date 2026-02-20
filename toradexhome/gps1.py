import gps
import matplotlib.pyplot as plt
import time

# conecta ao gpsd
session = gps.gps(mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

latitudes = []
longitudes = []

plt.ion()
fig, ax = plt.subplots()

print("Esperando fix do GPS...")

while True:
    try:
        report = session.next()

        # só pega dados TPV (position fix)
        if report['class'] == 'TPV':

            if hasattr(report, 'lat') and hasattr(report, 'lon'):
                lat = report.lat
                lon = report.lon

                print(f"Lat: {lat:.6f}  Lon: {lon:.6f}")

                latitudes.append(lat)
                longitudes.append(lon)

                ax.clear()
                ax.plot(longitudes, latitudes, marker='o')
                ax.set_xlabel("Longitude")
                ax.set_ylabel("Latitude")
                ax.set_title("Trajetória GPS em tempo real")

                plt.pause(0.01)

    except KeyError:
        pass
    except KeyboardInterrupt:
        break
    except StopIteration:
        session = None
        print("GPSD terminou")
        break
