/*
 * uart_fifo.hpp
 *
 *  Created on: Jun 14, 2021
 *      Author: Vlad
 */

#ifndef UART_FIFO_INC_UART_FIFO_UARTTXFIFO_H_
#define UART_FIFO_INC_UART_FIFO_UARTTXFIFO_H_

#include "lwrb/lwrb.h"
#include <stddef.h>

#include "stm32l4xx_hal.h"
#include "stm32l4xx_hal_uart.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

struct UartTxFifo
{
	UART_HandleTypeDef * const uart;
	uint8_t * const memory;
	const size_t memory_size;
	volatile size_t transfering_data_len;
	lwrb_t fifo;
};

#define UARTTXFIFO_DECLARE(name, huart, size) \
	uint8_t _buffer##name[size]; \
	struct UartTxFifo name = {.uart = &huart, .memory = _buffer##name, .memory_size = size};

int UartTxFifo_Init(struct UartTxFifo *inst);

int UartTxFifo_write(struct UartTxFifo *inst, const uint8_t *data, size_t len);

void UartTxFifo_hal_cb(struct UartTxFifo *inst);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* UART_FIFO_INC_UART_FIFO_UARTTXFIFO_H_ */
