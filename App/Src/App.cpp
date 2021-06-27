/*
 * App.cpp
 *
 *  Created on: May 14, 2021
 *      Author: Vlad
 */
#include <sp/SPMessage.hpp>
#include <Uart_fifo/UartTxFifo.h>
#include <cstdio>

#include "main.h"
#include "usart.h"
#include "App.hpp"
#include "DgbLog.hpp"
#include "Bus/bus_uart.h"
#include "sp/SPHandler.hpp"

#include "nanocobs/cobs.h"

#include "sk6812.h"
#include "LedStrip.hpp"


constexpr DgbLog Logger("App");

void hexdump(const uint8_t *buffer, unsigned int size, unsigned int width);

void App() {
	LOG_INF("App started");

	BUS_UART_Init();
	SPHandler::Init();

	LOG_INF("Device Address: %d", SPHandler::GetBusAddress());

	/* USER CODE END 2 */

	/* Infinite loop */
	/* USER CODE BEGIN WHILE */
	while (1) {
		/* USER CODE END WHILE */
		static bool printed =false;
		//if (BUS_UART_NewDataAvaiable())
		{
			size_t buff_size = BUS_UART_FIFO_GetSize();
			if(buff_size)
			{
				HAL_GPIO_WritePin(DEBUG2_GPIO_Port, DEBUG2_Pin, GPIO_PIN_SET);
				uint8_t buff[2048];
				BUS_UART_FIFO_Peek(buff, sizeof(buff));

				auto cobs_end = static_cast<const uint8_t*>(memchr(buff, 0x00, buff_size));
				if(cobs_end != NULL)
				{
					size_t msg_size = cobs_end - buff + 1;

					if(cobs_decode_inplace(buff, msg_size) == COBS_RET_SUCCESS)
					{
						auto buff_decoded = buff + 1;
						auto buff_decoded_size = msg_size - 2;
						const SPMessage msg(buff_decoded, buff_decoded_size);

						if(msg.GetStatus() == SPMessage::Status::Completed)
						{
							BUS_UART_FIFO_Skip(msg_size);

							SPMessageDecoder request(msg);

							SPMessage replyMsg;

							replyMsg.SetCommand(msg.GetCommand());
							replyMsg.SetDest(0x00);
							replyMsg.SetHandler(msg.GetHandler());

							SPMessageEncoder reply(replyMsg);

							int ret = SPHandler::Process(request, reply);
							if(ret == ESUCCESS)
							{
								if(msg.GetDest() == SPMessage::BROADCAST_ADDR)
								{
									LOG_DBG("Cannot send reply to broadcast request.");
								}
								else
								{
									size_t replyDataLen = reply.serializeSize();

									uint8_t replyData[replyDataLen + 2];
									replyData[0] = COBS_INPLACE_SENTINEL_VALUE;
									reply.serialize(&replyData[1], replyDataLen);
									replyData[sizeof(replyData) - 1] = COBS_INPLACE_SENTINEL_VALUE;

									if(cobs_encode_inplace(replyData, sizeof(replyData)) == COBS_RET_SUCCESS)
									{
										hexdump(replyData, sizeof(replyData), 16);
										//HAL_Delay(500);
										BUS_UART_SendMsgBlocking(replyData, sizeof(replyData));
									}
									else
									{
										LOG_ERR("Failed to encode response");
									}
								}

							}

							printed = false;
						}
						else
						{
							if(printed==false)
							{
								printf("pending data\r\n");
								printed= true;
							}
						}
					}
					else
					{
						LOG_WRN("Failed to decode cobs data. Skipping %d bytes", msg_size);
						BUS_UART_FIFO_Skip(msg_size);
					}
				}

				HAL_GPIO_WritePin(DEBUG2_GPIO_Port, DEBUG2_Pin, GPIO_PIN_RESET);
			}
		}

		if(LedStripInstance.ShouldUpdate())
		{
			if(LedStripInstance.Update() != ESUCCESS)
			{
				LOG_INF("Waiting ongoing to finsih");
				while(LedStripInstance.Update() == -EBUSY);
			}
			LOG_INF("LEDs updated");
		}
	}

}

