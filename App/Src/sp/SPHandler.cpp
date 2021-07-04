/*
 * SPHandler.cpp
 *
 *  Created on: Jun 7, 2021
 *      Author: Vlad
 */

#include "error.h"

#include "sp/SPHandler.hpp"
#include "DgbLog.hpp"
#include "main.h"

#include "LedStrip.hpp"

constexpr DgbLog Logger("SPHandler");

void hexdump(const uint8_t *buffer, unsigned int size, unsigned int width)
{
	unsigned int index = 0;
	unsigned int spacer = 0;

	if (size == 0)
		return;

	while (index < size)
	{
		printf("%04X  ", index);

		// Dont exceed maximum width, and calculate spacer
		if ((index + width) > size)
		{
			spacer = width - (size - index);
			width = size - index;
		}

		for (unsigned int i = 0; i < width; i++)
		{
			printf("%02x ", buffer[index + i]);
		}

		// Lign out last semicoln if spacer is calculated
		if (spacer > 0)
		{
			for (unsigned int i = 0; i < spacer; i++)
			{
				printf("__ ");
			}
		}

		printf(": ");

		for (unsigned int i = 0; i < width; i++)
		{
			if ((buffer[index + i] < 32) || (buffer[index + i] > 126))
			{
				printf(".");
			}
			else
			{
				printf("%c", buffer[index + i]);
			}
		}

		printf("\r\n");
		index += width;
	}
}

void SPHandler::PrintMessage(const std::string_view &label,
		const SPMessage &msg)
{
	printf("\r\n%s\r\n", label.data());
	printf("Dest: %d, Cmd: %d, Handler: %d Len: %d, Status: %d\r\n", msg.GetDest(),
			msg.GetCommand(), msg.GetHandler(), msg.GetLen(), (int) msg.GetStatus());

	hexdump(msg.GetDataLocation(), msg.GetLen(), 16);

	printf("\r\n");
}

int SPHandler::Process(SPMessageDecoder &request, SPMessageEncoder &reply)
{
	auto dest = request.GetMessage().GetDest();
	if (dest != GetBusAddress() && dest != SPMessage::BROADCAST_ADDR)
	{
		LOG_INF("Ignoring message for id %d", dest);
		return -EINVAL;
	}

	reply.GetMessage().SetDest(SPMessage::MASTER_ADDR);
	reply.GetMessage().SetCommand(request.GetMessage().GetCommand());
	reply.GetMessage().SetHandler(request.GetMessage().GetHandler());

	SPHandler::PrintMessage("Request", request.GetMessage());
	int ret = -ENOTSUP;

	switch (request.GetMessage().GetCommand())
	{
	case CMD_GET_POWER:
		ret = HandlerGetPower(request, reply);
		break;
	case CMD_SET_POWER:
		ret = HandlerSetPower(request, reply);
		break;
	case CMD_GET_LUMINOSITY:
		ret = HandlerGetLuminosity(request, reply);
		break;
	case CMD_SET_LUMINOSITY:
		ret = HandlerSetLuminosity(request, reply);
		break;

	case CMD_GET_STRIP_LEN:
		ret = HandlerGetStripLen(request, reply);
		break;

	case CMD_UPDATE_LED_COLOR:
		ret = HandlerUpdateLedColor(request, reply);
		break;

	case CMD_UPDATE_LED_PIXELS:
		ret = HandlerUpdateLedPixels(request, reply);
		break;

	case CMD_UPDATE_LED_PIXELS_WO_ACK:
		ret = HandlerUpdateLedPixels(request, reply);
		ret = ENODATA;
		break;

	case CMD_PING:
		ret = HandlerPing(request, reply);
		break;
	}

	if (ret == -ENOTSUP)
	{
		LOG_ERR("Failed to process request");
	}
	else
	{
		reply.Close();

		if(dest == SPMessage::BROADCAST_ADDR)
		{
			LOG_INF("No reply for broadcast request");
		}
		else
		{
			SPHandler::PrintMessage("Reply", reply.GetMessage());
		}
	}

	if(dest == SPMessage::BROADCAST_ADDR)
	{
		return ENODATA;
	}

	return ret;
}

int SPHandler::HandlerSetPower(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;
	uint8_t cmd;

	ret = request.decode(&cmd);
	RETURN_ON_ERROR(ret, decode);

	LedStripInstance.SetIsActive(cmd);

	if (cmd)
	{
		LOG_INF("Power on");
	}
	else
	{
		LOG_INF("Power off");
	}

	return ESUCCESS;
}

int SPHandler::HandlerGetPower(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;

	uint8_t power = LedStripInstance.IsActive();
	ret = reply.encode<uint8_t>(&power);
	RETURN_ON_ERROR(ret, encode);

	return ESUCCESS;
}

int SPHandler::HandlerSetLuminosity(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;
	uint8_t luminosity;

	ret = request.decode(&luminosity);
	RETURN_ON_ERROR(ret, decode);

	LedStripInstance.SetLuminosity(luminosity);

	return ESUCCESS;
}

int SPHandler::HandlerGetLuminosity(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;

	uint8_t luminosity = LedStripInstance.GetLuminosity();
	ret = reply.encode<uint8_t>(&luminosity);
	RETURN_ON_ERROR(ret, encode);

	return ESUCCESS;
}

int SPHandler::HandlerGetStripLen(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;

	uint8_t strip_len = LedStripInstance.GetLength();
	ret = reply.encode<uint8_t>(&strip_len);
	RETURN_ON_ERROR(ret, encode);

	return ESUCCESS;
}

int SPHandler::HandlerUpdateLedColor(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;
	uint8_t r, g, b;

	ret = request.decode(&r);
	RETURN_ON_ERROR(ret, decode);

	ret = request.decode(&g);
	RETURN_ON_ERROR(ret, decode);

	ret = request.decode(&b);
	RETURN_ON_ERROR(ret, decode);

	LOG_INF("%s %d, %d, %d", __func__, r, g, b);

	LedStripInstance.SetColor(r, g, b);

	return ESUCCESS;
}

int SPHandler::HandlerUpdateLedPixels(SPMessageDecoder &request,
		SPMessageEncoder &reply)
{
	int ret;

	uint8_t reqLedConunt;

	ret = request.decode(&reqLedConunt);
	RETURN_ON_ERROR(ret, decode);

	uint8_t ledCount = std::min(LedStripInstance.GetLength(), reqLedConunt);
	if (ledCount != LedStripInstance.GetLength())
	{
		LOG_WRN("LED count mismatch: got %d, expected %d", ledCount,
				LedStripInstance.GetLength());
	}

	uint8_t bytesPerLed = request.GetMessage().GetLen() / ledCount;
	if (bytesPerLed != LedStripInstance.GetBytesPerPixel())
	{
		LOG_WRN("Bytes per LED mismatch: got %d, expected %d", bytesPerLed,
				LedStripInstance.GetBytesPerPixel());
	}

	LOG_INF("%s Led: %d, Bytes/Led: %d", __func__, ledCount, bytesPerLed);

	for (auto i = 0; i < ledCount; i++)
	{
		uint8_t r, g, b;

		ret = request.decode(&r);
		RETURN_ON_ERROR(ret, decode);

		ret = request.decode(&g);
		RETURN_ON_ERROR(ret, decode);

		ret = request.decode(&b);
		RETURN_ON_ERROR(ret, decode);

		LedStripInstance.SetColor(i, r, g, b);
	}

	return ESUCCESS;
}

int SPHandler::HandlerPing(SPMessageDecoder &request, SPMessageEncoder &reply)
{
	LOG_INF("Ping received from %d", request.GetMessage().GetDest());

	if(request.GetMessage().GetDest() == SPMessage::BROADCAST_ADDR)
	{
		LOG_WRN("Broadcast ping");
	}

	return ESUCCESS;
}

uint8_t SPHandler::ReadBusAddress()
{
	// Read GPIO configuration pins (!PULL-UP)
	uint8_t pin1State = !(HAL_GPIO_ReadPin(BUS_ADDR0_GPIO_Port, BUS_ADDR0_Pin));
	uint8_t pin2State = !(HAL_GPIO_ReadPin(BUS_ADDR1_GPIO_Port, BUS_ADDR1_Pin));
	uint8_t pin3State = !(HAL_GPIO_ReadPin(BUS_ADDR2_GPIO_Port, BUS_ADDR2_Pin));
	uint8_t pin4State = !(HAL_GPIO_ReadPin(BUS_ADDR3_GPIO_Port, BUS_ADDR3_Pin));

	// Create a 4bit value out of the read pins
	uint8_t addr = (pin4State << 3) + (pin3State << 2) + (pin2State << 1) + pin1State;
	return addr;
}
