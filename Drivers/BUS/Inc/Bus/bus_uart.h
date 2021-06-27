/*
 * bus_uart.h
 *
 *  Created on: May 20, 2021
 *      Author: Vlad
 */

#ifndef BUS_INC_BUS_UART_H_
#define BUS_INC_BUS_UART_H_

#ifdef __cplusplus
extern "C" {
#endif

/* Includes */
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
/* Defines */

/* @brief   Defines the maximum size of the TEST MESSAGE BUFFER
 *          4 block of 256 (1024 bytes) + 4 bytes (First Frame) + 1 byte (lwrb lib requirement)
 */
#define BUS_MESSAGE_LENGTH_MAX 1024

/* Enums -----------------------------------------------------------------------*/

/* Global variables */

/* Public Function Declaration */

/* FIFO FUNCTIONS */
/*************************************TEST_UART_FIFO_GetSize**************************************************
 **
 * @brief   Returns the number of bytes currently available in buffer.
 * @param   none
 * @retval  number of bytes
 */
size_t BUS_UART_FIFO_GetSize(void);

/*************************************TEST_UART_FIFO_Peek**************************************************
 **
 * @brief       Read from buffer without changing read pointer (peek only)
 * @param[out]  *outputData - bytes read are passed in outputData
 * @param[in]   size - number of bytes requested
 * @retval      number of bytes peeked and written to outputData array
 */
size_t BUS_UART_FIFO_Peek(uint8_t *outputData, size_t size);

/*************************************TEST_UART_FIFO_Skip**************************************************
 **
 * @brief   Returns the number of bytes currently available in buffer.
 * @param   size
 * @retval  number of bytes skipped
 */
size_t BUS_UART_FIFO_Skip(size_t size);

/*************************************TEST_UART_FIFO_GetData**************************************************
 **
 * @brief       Read data from buffer. Copies data from buffer to data array and marks buffer as free for maximum
 *              'size' number of bytes.
 * @param[out]  *outputData - bytes read are passed in outputData
 * @param[in]   size - number of bytes requested
 * @retval      Number of bytes read and copied to data array
 */
size_t BUS_UART_FIFO_GetData(uint8_t *outputData, size_t size);

/*************************************TEST_UART_SendMsg**************************************************
 **
 * @brief   Function that calls the HAL_UART_Transmit_IT to send a message through UART
 * @param   user_data - the data that will be sent (ASCII or HEX format)
 * @param   size - works as a default parameter. If size is 0, the length of the message is
 *          calculated using the 'strlen' function (works for strings)
 * @retval  bool type - success / fail
 */
bool BUS_UART_SendMsgBlocking(const uint8_t *userData, uint16_t size);

/*************************************TEST_UART_Init**************************************************
 **
 * @brief   Start listening on UART in DMA mode and IDLE LINE detection
 * @param   baudrate
 * @retval  bool type - success / fail
 */
int BUS_UART_Init();

bool BUS_UART_NewDataAvaiable();

#ifdef __cplusplus
}
#endif

#endif /* BUS_INC_BUS_UART_H_ */
