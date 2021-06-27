/*
 * SPHandler.hpp
 *
 *  Created on: Jun 7, 2021
 *      Author: Vlad
 */

#ifndef INC_SP_SPHANDLER_HPP_
#define INC_SP_SPHANDLER_HPP_

#include <string_view>

#include "sp/SPMessage.hpp"

class SPHandler
{
public:

	static uint8_t GetBusAddress() { return DEVICE_ADDRESS; }

	static int Init()
	{
		DEVICE_ADDRESS = ReadBusAddress();
		return 0;
	}

	static int Process(SPMessageDecoder &request, SPMessageEncoder &reply);



private:
	static uint8_t ReadBusAddress();

	static constexpr uint16_t SetRequest(uint16_t req) {return req & 0x0100; }

	static void PrintMessage(const std::string_view &label, const SPMessage &msg);

	static int HandlerSetPower(SPMessageDecoder &request, SPMessageEncoder &reply);
	static int HandlerGetPower(SPMessageDecoder &request, SPMessageEncoder &reply);

	static int HandlerSetLuminosity(SPMessageDecoder &request, SPMessageEncoder &reply);
	static int HandlerGetLuminosity(SPMessageDecoder &request, SPMessageEncoder &reply);

	static int HandlerGetStripLen(SPMessageDecoder &request, SPMessageEncoder &reply);

	static int HandlerUpdateLedColor(SPMessageDecoder &request, SPMessageEncoder &reply);
	static int HandlerUpdateLedPixels(SPMessageDecoder &request, SPMessageEncoder &reply);

	static int HandlerPing(SPMessageDecoder &request, SPMessageEncoder &reply);
public:
	inline static uint16_t DEVICE_ADDRESS = SPMessage::INVALID_DEST;

	constexpr inline static uint16_t CMD_SET_POWER = 0x01;
	constexpr inline static uint16_t CMD_GET_POWER = CMD_SET_POWER | 0x0100;//SetRequest(CMD_SET_POWER);
	constexpr inline static uint16_t CMD_SET_LUMINOSITY = 0x03;
	constexpr inline static uint16_t CMD_GET_LUMINOSITY = CMD_SET_LUMINOSITY | 0x0100;//SetRequest(CMD_SET_POWER);

	constexpr inline static uint16_t CMD_SET_STRIP_LEN = 0x02;
	constexpr inline static uint16_t CMD_GET_STRIP_LEN = CMD_SET_STRIP_LEN | 0x0100;//SetRequest(CMD_SET_POWER);

	constexpr inline static uint16_t CMD_UPDATE_LED_COLOR = 0x1000;
	constexpr inline static uint16_t CMD_UPDATE_LED_PIXELS = 0x1001;

	constexpr inline static uint16_t CMD_PING = 0xA000;

};


#endif /* INC_SP_SPHANDLER_HPP_ */
