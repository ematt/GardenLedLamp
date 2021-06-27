/*
 * UartTxFifo.cpp
 *
 *  Created on: Jun 14, 2021
 *      Author: Vlad
 */

#include <Uart_fifo/UartTxFifo.h>
#include "main.h"
#include "usart.h"

int UartTxFifo_Init(struct UartTxFifo *inst)
{
	lwrb_init(&inst->fifo, inst->memory, inst->memory_size);

	return 0;
}

static void UartTxFifo_start_transfer(struct UartTxFifo *inst)
{
	// Return if a transfer is already in progress
	if (inst->transfering_data_len != 0)
		return;

	inst->transfering_data_len = lwrb_get_linear_block_read_length(&inst->fifo);
	uint8_t *data = (uint8_t*) lwrb_get_linear_block_read_address(&inst->fifo);

	HAL_UART_Transmit_IT(inst->uart, data, inst->transfering_data_len);
}

int UartTxFifo_write(struct UartTxFifo *inst, const uint8_t *data, size_t len)
{
	lwrb_write(&inst->fifo, data, len);
	UartTxFifo_start_transfer(inst);

	return len;
}

void UartTxFifo_hal_cb(struct UartTxFifo *inst)
{
	lwrb_skip(&inst->fifo, inst->transfering_data_len);
	inst->transfering_data_len = 0;

	UartTxFifo_start_transfer(inst);
}
