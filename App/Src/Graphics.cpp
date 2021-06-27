/*
 * Graphics.cpp
 *
 *  Created on: Jun 12, 2021
 *      Author: Vlad
 */

#include "Graphics.hpp"

ColorRGB::ColorRGB(const ColorHSV &hsv)
{
	uint8_t region, remainder, p, q, t;

	if (hsv.s == 0)
	{
		r = hsv.v;
		g = hsv.v;
		b = hsv.v;
		return;
	}

	region = hsv.h / 43;
	remainder = (hsv.h - (region * 43)) * 6;

	p = (hsv.v * (255 - hsv.s)) >> 8;
	q = (hsv.v * (255 - ((hsv.s * remainder) >> 8))) >> 8;
	t = (hsv.v * (255 - ((hsv.s * (255 - remainder)) >> 8))) >> 8;

	switch (region)
	{
	case 0:
		r = hsv.v;
		g = t;
		b = p;
		break;
	case 1:
		r = q;
		g = hsv.v;
		b = p;
		break;
	case 2:
		r = p;
		g = hsv.v;
		b = t;
		break;
	case 3:
		r = p;
		g = q;
		b = hsv.v;
		break;
	case 4:
		r = t;
		g = p;
		b = hsv.v;
		break;
	default:
		r = hsv.v;
		g = p;
		b = q;
		break;
	}
}

ColorHSV::ColorHSV(const ColorRGB &rgb)
{
	uint8_t rgbMin, rgbMax;

	rgbMin =
			rgb.r < rgb.g ?
					(rgb.r < rgb.b ? rgb.r : rgb.b) :
					(rgb.g < rgb.b ? rgb.g : rgb.b);
	rgbMax =
			rgb.r > rgb.g ?
					(rgb.r > rgb.b ? rgb.r : rgb.b) :
					(rgb.g > rgb.b ? rgb.g : rgb.b);

	v = rgbMax;
	if (v == 0)
	{
		h = 0;
		s = 0;
		return;
	}

	s = 255 * (long) (rgbMax - rgbMin) / v;
	if (s == 0)
	{
		h = 0;
		return;
	}

	if (rgbMax == rgb.r)
		h = 0 + 43 * (rgb.g - rgb.b) / (rgbMax - rgbMin);
	else if (rgbMax == rgb.g)
		h = 85 + 43 * (rgb.b - rgb.r) / (rgbMax - rgbMin);
	else
		h = 171 + 43 * (rgb.r - rgb.g) / (rgbMax - rgbMin);

}

