/*
 * LedStrip.hpp
 *
 *  Created on: Jun 10, 2021
 *      Author: Vlad
 */

#ifndef INC_LEDSTRIP_HPP_
#define INC_LEDSTRIP_HPP_

#include <cstdint>
#include <limits>
#include "error.h"

#include "sk6812.h"
#include "Graphics.hpp"

class LedStrip
{
public:
	constexpr static inline uint8_t MAX_LED_STRIP_LEN = NUM_PIXELS;

	constexpr uint8_t GetLength() const
	{
		return NUM_PIXELS;
	}
	constexpr uint8_t GetBytesPerPixel() const
	{
		return NUM_BPP;
	}

	constexpr bool IsActive() const
	{
		return _isActive;
	}
	constexpr void SetIsActive(bool value)
	{
		_isActive = value;
		_shouldUpdate = true;
	}

	constexpr auto GetLuminosity() const
	{
		return _luminosity;
	}
	constexpr void SetLuminosity(uint8_t value)
	{
		_luminosity = value;
		_shouldUpdate = true;
	}

	constexpr void SetColorCorrection(ColorRGB cc)
	{
		_colorCorrection = cc;
		_shouldUpdate = true;
	}

	constexpr ColorRGB GetColorCorrection() const
	{
		return _colorCorrection;
	}

	constexpr void SetColorTemperature(ColorRGB ct)
	{
		_colorTemperature = ct;
		_shouldUpdate = true;
	}

	constexpr ColorRGB GetColorTemperature() const
	{
		return _colorTemperature;
	}

	void SetColor(uint8_t r, uint8_t g, uint8_t b)
	{
		for (auto i = 0; i < GetLength(); i++)
		{
			leds[i].r = r;
			leds[i].g = g;
			leds[i].b = b;
		}

		_shouldUpdate = true;
	}

	void SetColor(uint8_t index, uint8_t r, uint8_t g, uint8_t b)
	{
		if (index >= MAX_LED_STRIP_LEN)
			return;

		leds[index].r = r;
		leds[index].g = g;
		leds[index].b = b;

		_shouldUpdate = true;
	}

	static inline uint8_t scale8(uint8_t x, uint8_t scale) {
	  return ((uint16_t)x * scale) >> 8;
	}

	int Update()
	{
		if (is_transfer_ongoing())
			return -EBUSY;

		if (!_isActive || gamma_lut[_luminosity] == 0x00)
		{
			led_set_all_RGB(0x00, 0x00, 0x00);
		}
		else
		{
			for (auto i = 0; i < GetLength(); i++)
			{
				const ColorRGB pixel = leds[i];
				ColorRGB c = computeAdjustment(gamma_lut[_luminosity], _colorCorrection, _colorTemperature);
				led_set_RGB(i, scale8(pixel.red, c.red), scale8(pixel.green, c.green), scale8(pixel.blue, c.blue));
			}
		}

		led_render();
		_shouldUpdate = false;

		return 0;
	}

	constexpr bool ShouldUpdate() const
	{
		return _shouldUpdate;
	}

private:
	bool _isActive = true;
	uint8_t _luminosity = 0xFF;
	ColorRGB _colorCorrection = TypicalPixelString;
	ColorRGB _colorTemperature = UncorrectedTemperature;
	bool _shouldUpdate = false;
	ColorRGB leds[MAX_LED_STRIP_LEN];

	// Gamma brightness lookup table <https://victornpb.github.io/gamma-table-generator>
	// gamma = 2.00 steps = 256 range = 0-255
	constexpr static inline uint8_t gamma_lut[256] =
	{ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2,
			2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9,
			9, 9, 10, 10, 11, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16,
			17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 23, 23, 24, 24, 25, 26,
			26, 27, 28, 28, 29, 30, 30, 31, 32, 32, 33, 34, 35, 35, 36, 37, 38,
			38, 39, 40, 41, 42, 42, 43, 44, 45, 46, 47, 47, 48, 49, 50, 51, 52,
			53, 54, 55, 56, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
			69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87,
			88, 89, 91, 92, 93, 94, 95, 97, 98, 99, 100, 102, 103, 104, 105,
			107, 108, 109, 111, 112, 113, 115, 116, 117, 119, 120, 121, 123,
			124, 126, 127, 128, 130, 131, 133, 134, 136, 137, 139, 140, 142,
			143, 145, 146, 148, 149, 151, 152, 154, 155, 157, 158, 160, 162,
			163, 165, 166, 168, 170, 171, 173, 175, 176, 178, 180, 181, 183,
			185, 186, 188, 190, 192, 193, 195, 197, 199, 200, 202, 204, 206,
			207, 209, 211, 213, 215, 217, 218, 220, 222, 224, 226, 228, 230,
			232, 233, 235, 237, 239, 241, 243, 245, 247, 249, 251, 253, 255, };

	// https://github.com/FastLED/FastLED/blob/b5874b588ade1d2639925e4e9719fa7d3c9d9e94/src/controller.h#L150
    static ColorRGB computeAdjustment(uint8_t scale, const ColorRGB & colorCorrection, const ColorRGB & colorTemperature) {
    	ColorRGB adj = 0;

		if(scale > 0) {
		  for(uint8_t i = 0; i < 3; ++i) {
			  uint8_t cc = colorCorrection.raw[i];
			  uint8_t ct = colorTemperature.raw[i];
			  if(cc > 0 && ct > 0) {
				  uint32_t work = (((uint32_t)cc)+1) * (((uint32_t)ct)+1) * scale;
				  work /= 0x10000L;
				  adj.raw[i] = work & 0xFF;
			  }
		  }
		}

		return adj;
    }

};

extern LedStrip LedStripInstance;

#endif /* INC_LEDSTRIP_HPP_ */
