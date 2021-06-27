/**
  ******************************************************************************
  * @file           : TEST_UART_Driver.h
  * @brief          : HAL Driver functions for the TEST Serial connection
  * @author         : Sebastian Popa, sebastian.popa@arobs.com
  * @date           : mar 2021
  *
  ******************************************************************************
  */
/* Includes */
#include <errno.h>
#include <lwrb/lwrb.h>


#include "Bus/bus_uart.h"
#include "usart.h"

#include "main.h"

/* Defines */
static UART_HandleTypeDef *const _uart_handler = &huart1;


#define FIFO_NO_SKIP            0

/* Static Variable Declarations */
static lwrb_t _fifoInstance;
static uint8_t _fifoBuffer[BUS_MESSAGE_LENGTH_MAX];
static size_t _lengthToWriteUART;
static uint8_t *_dataWriteAddressUART;
static volatile bool _isNewDataAvaiable;

/* Static function prototypes */

/* Function Declarations */

/* FIFO FUNCTIONS */
/**
 * @brief   Returns the number of bytes currently available in buffer.
 * @param   none
 * @retval  number of bytes
 */
size_t BUS_UART_FIFO_GetSize(void)
{
    return lwrb_get_full(&_fifoInstance);
}

 /**
 * @brief       Read from buffer without changing read pointer (peek only)
 * @param[out]  *outputData - bytes read are passed in outputData
 * @param[in]   size - number of bytes requested
 * @retval      number of bytes peeked and written to outputData array
 */
size_t BUS_UART_FIFO_Peek(uint8_t *outputData, size_t size)
{
    return lwrb_peek(&_fifoInstance, FIFO_NO_SKIP, outputData, size);
}

/**
 * @brief       Read data from buffer. Copies data from buffer to data array and marks buffer as free for maximum
 *              'size' number of bytes.
 * @param[out]  *outputData - bytes read are passed in outputData
 * @param[in]   size - number of bytes requested
 * @retval      Number of bytes read and copied to data array
 */
size_t BUS_UART_FIFO_GetData(uint8_t *outputData, size_t size)
{
    return lwrb_read(&_fifoInstance, outputData, size);
}
//
//uint8_t* BUS_UART_FIFO_GetDataLocation()
//{
//    return lwrb_read(&_fifoInstance, outputData, size);
//}


/**
 * @brief   Returns the number of bytes currently available in buffer.
 * @param   size
 * @retval  number of bytes skipped
 */
size_t BUS_UART_FIFO_Skip(size_t size)
{
    return lwrb_skip (&_fifoInstance, size);
}

/* Message Received Flag functions */

/**
 * @brief   Function that calls the HAL_UART_Transmit to send a message through UART in blocking mode
 * @param   user_data - the data that will be sent (ASCII or HEX format)
 * @param   size - works as a default parameter. If size is 0, the length of the message is
 *          calculated using the 'strlen' function (works for strings)
 * @retval  bool type - success / fail
 */
bool BUS_UART_SendMsgBlocking(const uint8_t *userData, uint16_t size)
{
    HAL_StatusTypeDef status = HAL_UART_Transmit(_uart_handler, (uint8_t*) userData, size, HAL_MAX_DELAY);
    return (status == HAL_OK);
}

/**
 * @brief   Init TEST UART peripheral, init FIFO, start listening in DMA, IDLE interrupt mode
 * @param   baudrate
 * @retval  bool type - success / fail
 */
int BUS_UART_Init()
{
    HAL_UART_DMAStop(_uart_handler);

    lwrb_init(&_fifoInstance, _fifoBuffer, sizeof(_fifoBuffer));
    _lengthToWriteUART = lwrb_get_linear_block_write_length(&_fifoInstance);
    _dataWriteAddressUART = lwrb_get_linear_block_write_address(&_fifoInstance);

    // Enable IDLE interrupt (check when bytes are not being received)
    __HAL_UART_CLEAR_IDLEFLAG(&huart1);
    __HAL_UART_ENABLE_IT(_uart_handler, UART_IT_IDLE);   // enable idle line interrupt

    // Start listening in interrupt mode
    HAL_StatusTypeDef status = HAL_UART_Receive_DMA(_uart_handler, _dataWriteAddressUART, _lengthToWriteUART);

    return status == HAL_OK ? 0 : -EIO;
}
/**
 * @brief
 * @param
 * @retval
 */
void BUS_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	//HAL_GPIO_TogglePin(DEBUG_GPIO_Port, DEBUG_Pin);
    uint32_t currentMsgLength;
    HAL_UART_DMAStop(huart);

    currentMsgLength = _lengthToWriteUART - __HAL_DMA_GET_COUNTER(huart->hdmarx);
    lwrb_advance(&_fifoInstance, currentMsgLength);

    // Check if this message is complete
    _isNewDataAvaiable = true;

    if ((_lengthToWriteUART = lwrb_get_linear_block_write_length(&_fifoInstance)) > 0)
    {
        _dataWriteAddressUART = lwrb_get_linear_block_write_address(&_fifoInstance);
        if(HAL_UART_Receive_DMA(_uart_handler, _dataWriteAddressUART, _lengthToWriteUART) != HAL_OK)
        {
        	__BKPT(0);
        }
    }
    else
    {
        /* FIFO FULL */
        assert_param(0);
    }
	//HAL_GPIO_TogglePin(DEBUG_GPIO_Port, DEBUG_Pin);
}

bool BUS_UART_NewDataAvaiable()
{
	bool r = _isNewDataAvaiable;
	_isNewDataAvaiable = false;
	return r;
}

/* End of File */
