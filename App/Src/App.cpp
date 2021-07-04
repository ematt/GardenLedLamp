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

void App_SP()
{
	while (true)
	{
		size_t buff_size = BUS_UART_FIFO_GetSize();
		if (buff_size == 0)
		{
			return;
		}

		uint8_t buff[2048];
		BUS_UART_FIFO_Peek(buff, sizeof(buff));

		auto cobs_end = static_cast<const uint8_t*>(memchr(buff, 0x00,
				buff_size));
		if (cobs_end == NULL)
		{
			return;
		}

		size_t msg_size = cobs_end - buff + 1;

		cobs_ret_t cd_ret = cobs_decode_inplace(buff, msg_size);
		BUS_UART_FIFO_Skip(msg_size);

		if (cd_ret != COBS_RET_SUCCESS)
		{
			LOG_ERR("Failed to decode cobs data. Skipping %d bytes", msg_size);
			return;
		}

		auto buff_decoded = buff + 1;
		auto buff_decoded_size = msg_size - 2;
		const SPMessage msg(buff_decoded, buff_decoded_size);

		if (msg.GetStatus() != SPMessage::Status::Completed)
		{
			LOG_ERR("Failed to parse data. Skipping %d bytes", msg_size);
			return;
		}

		SPMessageDecoder request(msg);
		SPMessage replyMsg;
		SPMessageEncoder reply(replyMsg);

		int ret = SPHandler::Process(request, reply);
		if (ret < ESUCCESS)
		{
			LOG_ERR("Failed to parse data. Skipping %d bytes", msg_size);
			return;
		}

		if (ret == ENODATA)
		{
			LOG_DBG("Empty reply.");
		}
		else
		{
			size_t replyDataLen = reply.serializeSize();

			uint8_t replyData[replyDataLen + 2];
			replyData[0] = COBS_INPLACE_SENTINEL_VALUE;
			reply.serialize(&replyData[1], replyDataLen);
			replyData[sizeof(replyData) - 1] = COBS_INPLACE_SENTINEL_VALUE;

			if (cobs_encode_inplace(replyData, sizeof(replyData))
					== COBS_RET_SUCCESS)
			{
				hexdump(replyData, sizeof(replyData), 16);
				BUS_UART_SendMsgBlocking(replyData, sizeof(replyData));
			}
			else
			{
				LOG_ERR("Failed to encode response");
			}
		}
	}
}

void App()
{
	LOG_INF("App started");

	BUS_UART_Init();
	SPHandler::Init();

	LOG_INF("Device Address: %d", SPHandler::GetBusAddress());

	LedStripInstance.SetColor(0x00, 0x00, 0x00);
	LedStripInstance.SetColor(0x00, 0xFF, 0xFF, 0xFF);

	while (1)
	{

		App_SP();

		if (LedStripInstance.ShouldUpdate())
		{
			if (LedStripInstance.Update() != ESUCCESS)
			{
				LOG_INF("Waiting ongoing to finsih");
				while (LedStripInstance.Update() == -EBUSY)
					;
			}
			LOG_INF("LEDs updated");
		}
	}

}

