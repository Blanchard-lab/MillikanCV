import numpy as np

class Calculator:
    
    def __init__(self, pixels_mm, pressure_torr, distance_mm=4.902):
        self.pixels_mm = pixels_mm
        self.pressure_torr = pressure_torr
        self.distance_m = distance_mm * 1e-3  # Convert mm to meters
        self.voltage = 500  # Applied voltage in volts
        self.E = self.voltage / self.distance_m  # Electric field strength
        self.roomtempc = 20  # Room temperature in Celsius
        self.density_oil = 0.861e3  # Corrected density of oil in kg/m^3
        self.a_gravity = 9.81  # Acceleration due to gravity in m/s^2
        self.vu = 0.00021081410768772413  # Upward velocity in m/s
        self.vd = 0.00007087091476466052  # Downward velocity in m/s
        self.viscosity_air = self.corrected_viscosity()  # Use corrected viscosity

    def corrected_viscosity(self):
        # Initial viscosity without correction
        eta_0 = 1.8228e-5 + ((4.790e-8) * (self.roomtempc - 21))
        # Radius without correction
        radius_uncorrected = np.sqrt((9 * eta_0 * self.vd) / (2 * self.density_oil * self.a_gravity))
        # Corrected viscosity
        correction_factor = 1 + (5.908e-5 / (radius_uncorrected * self.pressure_torr))
        return eta_0 / correction_factor
    
    def find_radius(self):
        top = (9 * self.viscosity_air * self.vd)
        bot = (2 * self.density_oil * self.a_gravity)
        radius = np.sqrt(top / bot)
        return radius

    def find_mass(self):
        radius = self.find_radius()
        top = self.density_oil * 4 * np.pi * np.power(radius, 3)
        bot = 3
        mass = top / bot
        return mass

    def find_charge(self):
        radius = self.find_radius()
        mass = self.find_mass()
        charge = ((mass * self.a_gravity) + (6 * np.pi * self.viscosity_air * radius * self.vu)) / self.E 
        return charge
    
def main():
    particle = Calculator(pixels_mm=414.20, pressure_torr=760, distance_mm=4.902)
    charge = particle.find_charge()
    print(f"Charge: {charge:.5e} C")
    integerM = charge / 1.602176634e-19
    print(f"Interval: {integerM: .5e} C")

if __name__ == "__main__":
    main()