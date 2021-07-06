/*
 * Graphcs.hpp
 *
 *  Created on: Jun 12, 2021
 *      Author: Vlad
 */

#ifndef INC_GRAPHICS_HPP_
#define INC_GRAPHICS_HPP_

#include <cstdint>

typedef enum
{
	// Color correction starting points

	/// typical values for SMD5050 LEDs
	///@{
	TypicalSMD5050 = 0xFFB0F0 /* 255, 176, 240 */,
	TypicalLEDStrip = 0xFFB0F0 /* 255, 176, 240 */,
	///@}

	/// typical values for 8mm "pixels on a string"
	/// also for many through-hole 'T' package LEDs
	///@{
	Typical8mmPixel = 0xFFE08C /* 255, 224, 140 */,
	TypicalPixelString = 0xFFE08C /* 255, 224, 140 */,
	///@}

	/// uncorrected color
	UncorrectedColor = 0xFFFFFF

} LEDColorCorrection;

typedef enum
{
	/// @name Black-body radiation light sources
	/// Black-body radiation light sources emit a (relatively) continuous
	/// spectrum, and can be described as having a Kelvin 'temperature'
	///@{
	/// 1900 Kelvin
	Candle = 0xFF9329 /* 1900 K, 255, 147, 41 */,
	/// 2600 Kelvin
	Tungsten40W = 0xFFC58F /* 2600 K, 255, 197, 143 */,
	/// 2850 Kelvin
	Tungsten100W = 0xFFD6AA /* 2850 K, 255, 214, 170 */,
	/// 3200 Kelvin
	Halogen = 0xFFF1E0 /* 3200 K, 255, 241, 224 */,
	/// 5200 Kelvin
	CarbonArc = 0xFFFAF4 /* 5200 K, 255, 250, 244 */,
	/// 5400 Kelvin
	HighNoonSun = 0xFFFFFB /* 5400 K, 255, 255, 251 */,
	/// 6000 Kelvin
	DirectSunlight = 0xFFFFFF /* 6000 K, 255, 255, 255 */,
	/// 7000 Kelvin
	OvercastSky = 0xC9E2FF /* 7000 K, 201, 226, 255 */,
	/// 20000 Kelvin
	ClearBlueSky = 0x409CFF /* 20000 K, 64, 156, 255 */,
	///@}

	/// @name Gaseous light sources
	/// Gaseous light sources emit discrete spectral bands, and while we can
	/// approximate their aggregate hue with RGB values, they don't actually
	/// have a proper Kelvin temperature.
	///@{
	WarmFluorescent = 0xFFF4E5 /* 0 K, 255, 244, 229 */,
	StandardFluorescent = 0xF4FFFA /* 0 K, 244, 255, 250 */,
	CoolWhiteFluorescent = 0xD4EBFF /* 0 K, 212, 235, 255 */,
	FullSpectrumFluorescent = 0xFFF4F2 /* 0 K, 255, 244, 242 */,
	GrowLightFluorescent = 0xFFEFF7 /* 0 K, 255, 239, 247 */,
	BlackLightFluorescent = 0xA700FF /* 0 K, 167, 0, 255 */,
	MercuryVapor = 0xD8F7FF /* 0 K, 216, 247, 255 */,
	SodiumVapor = 0xFFD1B2 /* 0 K, 255, 209, 178 */,
	MetalHalide = 0xF2FCFF /* 0 K, 242, 252, 255 */,
	HighPressureSodium = 0xFFB74C /* 0 K, 255, 183, 76 */,
	///@}

	/// Uncorrected temperature 0xFFFFFF
	UncorrectedTemperature = 0xFFFFFF
} ColorTemperature;

class ColorHSV;

class ColorRGB
{
public:

	inline ColorRGB() = default;
	inline ColorRGB(uint8_t r_, uint8_t g_, uint8_t b_) :
			r(r_), g(g_), b(b_)
	{
	}

	inline ColorRGB(uint32_t colorcode) :
			r((colorcode >> 16) & 0xFF), g((colorcode >> 8) & 0xFF), b(
					(colorcode >> 0) & 0xFF)
	{
	}

	inline ColorRGB(LEDColorCorrection colorcode) :
			r((colorcode >> 16) & 0xFF), g((colorcode >> 8) & 0xFF), b(
					(colorcode >> 0) & 0xFF)
	{
	}

	inline ColorRGB(ColorTemperature colorcode) :
			r((colorcode >> 16) & 0xFF), g((colorcode >> 8) & 0xFF), b(
					(colorcode >> 0) & 0xFF)
	{
	}

	ColorRGB(const ColorHSV &hsv);

	constexpr operator uint32_t() const { return (r << 16) | (g << 8) | b; }

	union
	{
		struct
		{
			union
			{
				uint8_t r;
				uint8_t red;
			};
			union
			{
				uint8_t g;
				uint8_t green;
			};
			union
			{
				uint8_t b;
				uint8_t blue;
			};
		};
		uint8_t raw[3];
	};
};

class ColorHSV
{
public:
	ColorHSV() = default;
	ColorHSV(const ColorRGB &rgb);

	union
	{
		struct
		{
			union
			{
				uint8_t h;
				uint8_t hue;
			};
			union
			{
				uint8_t s;
				uint8_t saturation;
			};
			union
			{
				uint8_t v;
				uint8_t value;
			};
		};
		uint8_t raw[3];
	};
};

#endif /* INC_GRAPHICS_HPP_ */
