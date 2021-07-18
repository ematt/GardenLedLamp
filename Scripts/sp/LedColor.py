import webcolors
from colormath.color_objects import sRGBColor, HSVColor
from colormath.color_conversions import convert_color

class LedColor:
    
    def __init__(self, r: int, g: int, b: int):
        super().__init__()
        self.r = int(r) & 0xFF
        self.g = int(g) & 0xFF
        self.b = int(b) & 0xFF

    @classmethod
    def fromColorName(cls, color):
        color_rgb = webcolors.html5_parse_legacy_color(color)
        return cls(color_rgb.red, color_rgb.green, color_rgb.blue)

    @classmethod
    def fromInt(cls, value: int):
        return cls( (value >> 16) & 255, (value >> 8) & 255, value & 255)

    @classmethod
    def fromTemperature(cls, colour_temperature: int):
        """
        Converts from K to RGB, algorithm courtesy of 
        http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
        """
        #range check
        if colour_temperature < 1000: 
            colour_temperature = 1000
        elif colour_temperature > 40000:
            colour_temperature = 40000
        
        tmp_internal = colour_temperature / 100.0
        
        # red 
        if tmp_internal <= 66:
            red = 255
        else:
            tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
            if tmp_red < 0:
                red = 0
            elif tmp_red > 255:
                red = 255
            else:
                red = tmp_red
        
        # green
        if tmp_internal <=66:
            tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
            if tmp_green < 0:
                green = 0
            elif tmp_green > 255:
                green = 255
            else:
                green = tmp_green
        else:
            tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
            if tmp_green < 0:
                green = 0
            elif tmp_green > 255:
                green = 255
            else:
                green = tmp_green
        
        # blue
        if tmp_internal >=66:
            blue = 255
        elif tmp_internal <= 19:
            blue = 0
        else:
            tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
            if tmp_blue < 0:
                blue = 0
            elif tmp_blue > 255:
                blue = 255
            else:
                blue = tmp_blue
        
        return cls(red, green, blue)

    @classmethod
    def fromHSV(cls, hsv: HSVColor):
        adobeRGB = convert_color(hsv, sRGBColor)
        pixel = adobeRGB.get_upscaled_value_tuple()
        return cls(*pixel)

    def toHSV(self) -> HSVColor:
        adobeRGB = sRGBColor(self.r, self.g, self.b, is_upscaled=True)
        hsv = convert_color(adobeRGB, HSVColor)
        return  hsv

    def __int__(self):
        return (self.r<<16) + (self.g<<8) + self.b

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, LedColor):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False

    def __repr__(self):
        return "<R:{} G:{} G:{}>".format(self.r, self.g, self.b)

def colorwheel(pos):
    """Colorwheel is built into CircuitPython's _pixelbuf. A separate colorwheel is included
    here for use with CircuitPython builds that do not include _pixelbuf, as with some of the
    SAMD21 builds. To use: input a value 0 to 255 to get a color value.
    The colours are a transition from red to green to blue and back to red."""
    pos = pos % 255
    if pos < 0 or pos > 255:
        return LedColor(0, 0, 0)
    if pos < 85:
        return LedColor(int(255 - pos * 3), int(pos * 3), 0)
    if pos < 170:
        pos -= 85
        return LedColor(0 , int(255 - pos * 3), int(pos * 3))
    pos -= 170
    return LedColor(pos * 3, 0, 255 - (pos * 3))

