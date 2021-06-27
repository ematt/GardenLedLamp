/*
 * Graphcs.hpp
 *
 *  Created on: Jun 12, 2021
 *      Author: Vlad
 */

#ifndef INC_GRAPHICS_HPP_
#define INC_GRAPHICS_HPP_

#include <cstdint>

class ColorHSV;

class ColorRGB
{
public:

	ColorRGB() = default;
	ColorRGB(const ColorHSV& hsv);

	uint8_t r;
	uint8_t g;
	uint8_t b;
};

class ColorHSV
{
public:
	ColorHSV() = default;
	ColorHSV(const ColorRGB& rgb);

	uint8_t h;
	uint8_t s;
	uint8_t v;
};


#endif /* INC_GRAPHICS_HPP_ */
