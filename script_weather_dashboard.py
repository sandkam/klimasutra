import requests
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import geocoder
import math

from datetime import datetime
from astral.sun import sun
from astral import Observer
from datetime import date
from timezonefinder import TimezoneFinder
from matplotlib.patches import Wedge


# Get location based on your public IP
g = geocoder.ip('me')

# --- 1) Location ---
latitude  = g.latlng[0]     #51.0344
longitude = g.latlng[1]     #7.0196
city      = g.city
country   = g.country

# --- Get timezone from lat/lon ---
tf = TimezoneFinder()
tz = tf.timezone_at(lat=latitude, lng=longitude)

if tz is None:
    tz = "Europe/Berlin"  # fallback


# --- Get sunrise and sunset time ---
observer = Observer(latitude=latitude, longitude=longitude)
s = sun(observer, date=date.today(), tzinfo=tz)

sunrise_H = s['sunrise'].hour
sunrise_M = s['sunrise'].minute
sunset_H = s['sunset'].hour
sunset_M = s['sunset'].minute
# -----------------------------------

# --- 2) Fetch data ---
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation,winddirection_10m,windspeed_10m,weathercode&timezone={tz}"
data = requests.get(url).json()

times = data["hourly"]["time"]
temps = data["hourly"]["temperature_2m"]
precs = data["hourly"]["precipitation"]
wind_dirs = data["hourly"]["winddirection_10m"]
wind_speeds = data["hourly"]["windspeed_10m"]
weather_codes = data["hourly"]["weathercode"]

# --- 3) Today selection ---
now = datetime.now()
today_str = now.strftime("%Y-%m-%d")
indices = [i for i, t in enumerate(times) if t.startswith(today_str)]

temp_vals = [temps[i] for i in indices]
prec_vals = [precs[i] for i in indices]
wind_d_vals = [wind_dirs[i] for i in indices]
wind_s_vals = [wind_speeds[i] for i in indices]
weather_today = [weather_codes[i] for i in indices]
time_labels = [times[i][11:16] for i in indices]


# --- 4) Current time interpolation ---
current_hour = now.hour
current_minute = now.minute
x_pos = current_hour + current_minute / 60.0

# Linear interpolation for temperature
t0, t1 = temp_vals[current_hour], temp_vals[current_hour + 1]
frac = current_minute / 60
current_temp = t0 + (t1 - t0) * frac

# --- 5) Current weather ---
weather_map = {
    0: "Clear sky", 1: "Almost clear sky", 2: "Partly cloudy", 3: "Cloudy",
    45: "Fog", 51: "Drizzle", 61: "Rain_L.", 63: "Rain_M.", 65: "Rain_H",
    71: "Snow_L", 73: "Snow_M", 75: "Snow_H", 95: "Thunderstorm",
}
current_weather = weather_map.get(weather_today[current_hour], "Unknown")

# --- 6) Icon ---
current_total = current_hour * 60 + current_minute
sunset_total  = sunset_H * 60 + sunset_M

if current_total <= sunset_total:
    icon_file_map = {
        0: "icons/0_clear_day.png", 1:"icons/1_mainly_clear_day.png", 2:"icons/2_partly_cloudy_day.png",
        3:"icons/3_cloudy.png", 45:"icons/45_fog.png", 51:"icons/51_drizzle.png",
        61:"icons/61_rain_L.png", 63:"icons/63_rain_M.png", 65:"icons/65_rain_H.png",
        71:"icons/71_snow_L.png", 73:"icons/73_snow_M.png", 75:"icons/75_snow_H.png",
        95:"icons/95_thunderstorm.png",
    }
else:
    icon_file_map = {
        0: "icons/0_clear_night.png", 1:"icons/1_mainly_clear_night.png", 2:"icons/2_partly_cloudy_night.png",
        3:"icons/3_cloudy.png", 45:"icons/45_fog.png", 51:"icons/51_drizzle.png",
        61:"icons/61_rain_L.png", 63:"icons/63_rain_M.png", 65:"icons/65_rain_H.png",
        71:"icons/71_snow_L.png", 73:"icons/73_snow_M.png", 75:"icons/75_snow_H.png",
        95:"icons/95_thunderstorm.png",
    }
icon_path = icon_file_map.get(weather_today[current_hour], "icons/0_default.png")

# --- 7) Figure layout ---
fig = plt.figure(figsize=(12,8))
gs = fig.add_gridspec(2,1, height_ratios=[1,1])

# --- Top half: 1x3 layout ---
gs_top = gs[0].subgridspec(1,3, width_ratios=[1,1,1])

# Location + temp
ax_loc = fig.add_subplot(gs_top[0])
ax_loc.axis('off')
ax_loc.text(0.5, 0.6, f"{city}, {country}", ha='center', va='center', fontsize=16, fontweight='bold')
ax_loc.text(0.5, 0.3, f"{current_temp:.1f} °C", ha='center', va='center', fontsize=14)

# Weather icon + title
ax_icon = fig.add_subplot(gs_top[1])
img = mpimg.imread(icon_path)
ax_icon.imshow(img)
ax_icon.set_title(current_weather, fontsize=14)
ax_icon.axis('off')

# Wind compass
ax_wind = fig.add_subplot(gs_top[2], polar=True)
wind_s_current = wind_s_vals[current_hour]
wind_d_current = wind_d_vals[current_hour]
angle_rad = np.deg2rad((wind_d_current + 180) % 360)
ax_wind.set_theta_zero_location('N')
ax_wind.set_theta_direction(-1)
ax_wind.set_rticks([])
# --- Compass labels ---
angles = np.arange(0, 360, 45)
labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
ax_wind.set_thetagrids(angles, labels)
# ----------------------
ax_wind.set_title(f"Wind: {wind_s_current} kph", fontsize=12)
ax_wind.annotate('', xy=(angle_rad, 1), xytext=(0,0),
                 arrowprops=dict(facecolor='red', width=3, headwidth=10))

# --- Bottom half: temp + precipitation ---
ax1 = fig.add_subplot(gs[1])
ax2 = ax1.twinx()

#hour_labels = list(range(24))
ax1.plot(time_labels, temp_vals, marker='o', label="Temp (°C)", color='tab:blue')
ax2.bar(time_labels, prec_vals, alpha=0.3, label="Precip (mm)", color='tab:cyan')

# Current time line
ax1.axvline(x=x_pos, color='r', linestyle='--', alpha=0.5)

# Labels
ax1.set_xlabel("Hour")
ax1.set_ylabel("Temperature (°C)")
ax2.set_ylabel("Precipitation (mm)")
ax1.set_title("Hourly Temperature & Precipitation")
#ax1.grid(True)
ax1.grid(True, axis='y', alpha=0.6)

# --- yaxis adjustments ---
ymin = math.floor(min(temp_vals)) - 1
ymax = math.ceil(max(temp_vals)) + 1
xmin = -1
xmax = 24
ax1.set_ylim(ymin,ymax)
ax1.set_xlim(xmin,xmax)
radius = 0.5  # adjust depending on your y-range

x_range = xmax - xmin
y_range = ymax - ymin

radius_y = 0.5
radius_x = radius_y * (y_range / x_range)  # scale x-radius to match y
# -------------------------

# Convert sunrise/sunset to fractional hours
sunrise_x = sunrise_H + sunrise_M / 60
sunset_x  = sunset_H  + sunset_M  / 60

# --- Sunrise semicircle (yellow) ---
theta = np.linspace(0, np.pi, 100)  # 0 -> 180 degrees
x = radius_y * np.cos(theta) * (y_range / x_range) + sunrise_x  # scale x to match y
y = radius_y * np.sin(theta) + ymin

ax1.fill_between(x, ymin, y, color='orange', alpha=0.4)

# --- Sunset semicircle (orange) ---
x = radius_y * np.cos(theta) * (y_range / x_range) + sunset_x  # scale x to match y
ax1.fill_between(x, ymin, y, color='red', alpha=0.8)


plt.tight_layout()
plt.show()
