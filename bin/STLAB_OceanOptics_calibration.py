from pyplr.calibrate import SpectraTuneLabSampler
from pyplr.oceanops import OceanOptics

# Connect to devices
oo = OceanOptics.from_first_available()
d = SpectraTuneLabSampler(password='***************', external=oo)

# Specify LEDs and intensities to be sampled
leds = [0, 1, 2, 3, 4, 5, 6 ,7 ,8 , 9]
intensities = [i for i in range(0, 4096, 65)]

# Sample
d.sample(leds=leds,
         intensities=intensities,
         external=oo,
         randomise=True)
d.make_dfs(save_csv=True)
