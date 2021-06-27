/*
 * error.h
 *
 *  Created on: Jun 27, 2021
 *      Author: Vlad
 */

#ifndef INC_ERROR_H_
#define INC_ERROR_H_

#ifdef __cplusplus
#include <cerrno>
#else
#include <errno.h>
#endif

#define ESUCCESS 0 ///< Value for success.

#endif /* INC_ERROR_H_ */
