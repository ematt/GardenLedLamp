/*
 * About.hpp
 *
 *  Created on: Jul 5, 2021
 *      Author: Vlad
 */

#include <string_view>
#include <cstdint>
#include <cstddef>
#include <cstring>

#include "stm32l4xx_hal.h"
#include "error.h"

#define DEVICE_MODEL "GL-18RGB"

#define _TEXTIFY(A) #A          ///< Internal macro used by TEXTIFY.
#define TEXTIFY(A) _TEXTIFY(A)  ///< Helper macro used to transform define int to string.

#define VERSION_MAJOR 0
#define VERSION_MINOR 0
#define VERSION_PATCH 0
#define VERSION_TAG "alpha"

#define VERSION_STRING   TEXTIFY(VERSION_MAJOR) "." TEXTIFY(VERSION_MINOR) "." TEXTIFY(VERSION_PATCH) "-" VERSION_TAG

static inline int ReadUUID(uint8_t *dest, size_t len)
{
	const size_t uuid_len = 3 * sizeof(uint32_t);
	if (uuid_len > len)
		return -ENOMEM;

	if( dest == nullptr)
		return -EINVAL;

	memcpy(dest, reinterpret_cast<const void*>(UID_BASE), uuid_len);

	return uuid_len;
}

