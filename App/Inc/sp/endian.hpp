/*
 * endian.hpp
 *
 *  Created on: Jun 6, 2021
 *      Author: Vlad
 */

#ifndef INC_SP_ENDIAN_HPP_
#define INC_SP_ENDIAN_HPP_

#define STRUCT_ENDIAN_NOT_SET   0
#define STRUCT_ENDIAN_BIG       1
#define STRUCT_ENDIAN_LITTLE    2

// Code from https://github.com/Tencent/rapidjson/blob/88bd956d66d348f478bceebfdadb8e26c6844695/include/rapidjson/rapidjson.h#L196

//! Endianness of the machine.
/*!
    \def BYTEORDER_ENDIAN
    GCC 4.6 provided macro for detecting endianness of the target machine. But other
    compilers may not have this. User can define BYTEORDER_ENDIAN to either
    \ref STRUCT_ENDIAN_LITTLE or \ref STRUCT_ENDIAN_BIG.
    Default detection implemented with reference to
    \li https://gcc.gnu.org/onlinedocs/gcc-4.6.0/cpp/Common-Predefined-Macros.html
    \li http://www.boost.org/doc/libs/1_42_0/boost/detail/endian.hpp
*/
#ifndef BYTEORDER_ENDIAN
    // Detect with GCC 4.6's macro.
#   if defined(__BYTE_ORDER__)
#       if (__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__)
#           define BYTEORDER_ENDIAN STRUCT_ENDIAN_LITTLE
#       elif (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#           define BYTEORDER_ENDIAN STRUCT_ENDIAN_BIG
#       else
#           error "Unknown machine byteorder endianness detected. User needs to define BYTEORDER_ENDIAN."
#       endif
    // Detect with GLIBC's endian.h.
#   elif defined(__GLIBC__)
#       include <endian.h>
#       if (__BYTE_ORDER == __LITTLE_ENDIAN)
#           define BYTEORDER_ENDIAN STRUCT_ENDIAN_LITTLE
#       elif (__BYTE_ORDER == __BIG_ENDIAN)
#           define BYTEORDER_ENDIAN STRUCT_ENDIAN_BIG
#       else
#           error "Unknown machine byteorder endianness detected. User needs to define BYTEORDER_ENDIAN."
#       endif
    // Detect with _LITTLE_ENDIAN and _BIG_ENDIAN macro.
#   elif defined(_LITTLE_ENDIAN) && !defined(_BIG_ENDIAN)
#       define BYTEORDER_ENDIAN STRUCT_ENDIAN_LITTLE
#   elif defined(_BIG_ENDIAN) && !defined(_LITTLE_ENDIAN)
#       define BYTEORDER_ENDIAN STRUCT_ENDIAN_BIG
    // Detect with architecture macros.
#   elif defined(__sparc) || defined(__sparc__) || defined(_POWER) || defined(__powerpc__) || defined(__ppc__) || defined(__hpux) || defined(__hppa) || defined(_MIPSEB) || defined(_POWER) || defined(__s390__)
#       define BYTEORDER_ENDIAN STRUCT_ENDIAN_BIG
#   elif defined(__i386__) || defined(__alpha__) || defined(__ia64) || defined(__ia64__) || defined(_M_IX86) || defined(_M_IA64) || defined(_M_ALPHA) || defined(__amd64) || defined(__amd64__) || defined(_M_AMD64) || defined(__x86_64) || defined(__x86_64__) || defined(_M_X64) || defined(__bfin__)
#       define BYTEORDER_ENDIAN STRUCT_ENDIAN_LITTLE
#   elif defined(_MSC_VER) && (defined(_M_ARM) || defined(_M_ARM64))
#       define BYTEORDER_ENDIAN STRUCT_ENDIAN_LITTLE
#   else
#       error "Unknown machine byteorder endianness detected. User needs to define BYTEORDER_ENDIAN."
#   endif
#endif


constexpr inline void endian_native_copy(void *dest, const void *src, size_t num)
{
    //memcpy(dest, src, num);
    char *d = (char*)dest;
    const char *s = (char*)src;

    while (num--)
        *d++ = *s++;
}

constexpr inline void endian_alternative_copy(void *dest, const void *src, size_t num)
{
    char *d = (char*)dest + num - 1;
    const char *s = (char*)src;

    while (num--)
        *d-- = *s++;
}

#endif /* INC_SP_ENDIAN_HPP_ */
