/*
 * sp.hpp
 *
 *  Created on: May 13, 2021
 *      Author: Vlad
 */

#ifndef INC_SPMESSAGE_HPP_
#define INC_SPMESSAGE_HPP_

#include <string>
#include <cstdint>
#include <cstring>
#include "error.h"
#include "sp/crc32.hpp"
#include "sp/endian.hpp"

class SPMessage {
public:
	enum class Status {
		Completed, NoMagic, TooShort, InvalidCrc, PayloadExceeded
	};

	constexpr SPMessage() {
	}

	constexpr SPMessage(const uint8_t raw_data[], size_t raw_len) {
		_status = parseData(raw_data, raw_len, _dest, _cmd, _handler, _crc, _data,
				sizeof(_data), _len);
	}

	static constexpr uint32_t CalculateCRC(const uint8_t data[], size_t len) {
		return crcdetail::compute(data, len);
	}

	static constexpr size_t GetHeaderSize() {
		return sizeof(MAGIC) + sizeof(_dest) + sizeof(_cmd) + sizeof(_handler);
	}

	static constexpr size_t GetFooterSize() {
		return sizeof(_crc);
	}

	static constexpr int findMagicBytes(const uint8_t data[], size_t len) {
		if (sizeof(MAGIC) > len)
			return -EINVAL;

		for (size_t j = 0; j < len - sizeof(MAGIC); j++) {
			size_t bytesFound = 0;
			for (size_t i = 0; i < sizeof(MAGIC); i++) {
				if (data[j + i] == MAGIC[i])
					bytesFound++;
			}

			if (bytesFound == sizeof(MAGIC))
				return j;
		}

		return -EBADMSG;
	}

	static constexpr void copyPayload(const uint8_t data[], size_t len,
			uint8_t dest[], size_t dest_len) {
		endian_native_copy(dest, data, len);
	}

	static inline void unpack_data(const void *bp, void *dst, size_t size) {
		endian_native_copy(dst, bp, size);
	}

	static inline void pack_data(void *bp, const void *dst, size_t size) {
		endian_native_copy(bp, dst, size);
	}

	static constexpr Status parseData(const uint8_t data[], size_t len,
			uint8_t &dest, uint16_t &cmd, uint8_t &handler, uint32_t &crc, uint8_t msgData[],
			uint16_t msgDataLen, uint16_t &msgLen) {
		int startIndex = findMagicBytes(data, len);
		if (startIndex < 0) {
			return Status::NoMagic;
		}
		len = len - startIndex;

		if (len > msgDataLen) {
			return Status::PayloadExceeded;
		}

		if (len < GetHeaderSize() + GetFooterSize()) {
			return Status::TooShort;
		}

		const uint8_t *rawMsg = &data[startIndex];

		size_t msgCrcLen = len - GetFooterSize();
		uint32_t calc_crc = CalculateCRC(rawMsg, msgCrcLen);
		crc = 0;

		unpack_data(&rawMsg[len - sizeof(uint32_t)], &crc, sizeof(crc));

		if (calc_crc != crc) {
			return Status::InvalidCrc;
		}

		// Valid message. Decode it
		unpack_data(&rawMsg[2], &dest, sizeof(dest));
		unpack_data(&rawMsg[3], &cmd, sizeof(cmd));
		unpack_data(&rawMsg[5], &handler, sizeof(handler));

		msgLen = len - GetHeaderSize() - GetFooterSize();
		copyPayload(&rawMsg[GetHeaderSize()], msgLen, msgData, msgLen);

		return Status::Completed;
	}

	constexpr bool isForMe() const {
		return _dest == 0x01;
	}

	constexpr auto GetDest() const {
		return _dest;
	}

	constexpr auto GetCommand() const {
		return _cmd;
	}

	constexpr auto GetHandler() const {
		return _handler;
	}

	constexpr auto GetLen() const {
		return _len;
	}
	constexpr auto GetStatus() const {
		return _status;
	}
	constexpr auto GetData(uint16_t i) const {
		return _data[i];
	}

	constexpr auto GetDataLocation() {
		return _data;
	}

	constexpr auto GetDataLocation() const {
		return _data;
	}

	constexpr size_t GetMaxLen() const {
		return sizeof(_data);
	}

	constexpr auto GetCrc() const {
		return _crc;
	}

	constexpr void SetDest(uint8_t dest) {
		_dest = dest;
	}

	constexpr void SetCommand(uint16_t cmd) {
		_cmd = cmd;
	}

	constexpr void SetHandler(uint16_t handler) {
		_handler = handler;
	}

	constexpr void SetLen(size_t len) {
		_len = len;
	}

	void write(size_t index, const uint8_t *data, size_t len) {
		copyPayload(data, len, &_data[index], len);
	}

	void Close() {
		_crc = 0;
		_crc = crcdetail::compute(MAGIC, sizeof(MAGIC));
		_crc = crcdetail::compute(&_dest, sizeof(_dest), _crc);
		_crc = crcdetail::compute(reinterpret_cast<const uint8_t*>(&_cmd),
				sizeof(_cmd), _crc);
		_crc = crcdetail::compute(&_handler, sizeof(_handler), _crc);
		_crc = crcdetail::compute(_data, _len, _crc);
	}


private:
	uint8_t _dest = INVALID_DEST;
	uint8_t _handler = INVALID_HANDLER;
	uint16_t _cmd = INVALID_CMD;
	uint32_t _crc = 0;
	uint16_t _len = 0;
	uint8_t _data[1024] = { 0 };
	Status _status = Status::NoMagic;

public:
	static constexpr inline uint8_t MAGIC[] = { 'S', 'P' };
	static constexpr inline decltype(_dest) INVALID_HANDLER = std::numeric_limits<
			decltype(_handler)>::min();
	static constexpr inline decltype(_cmd) INVALID_CMD = std::numeric_limits<
			decltype(_cmd)>::max();

	static constexpr inline decltype(_dest) INVALID_DEST = std::numeric_limits<
			decltype(_dest)>::max();
	static constexpr inline decltype(_dest) BROADCAST_ADDR = std::numeric_limits<
			decltype(_dest)>::max()-1;
};

class SPMessageDecoder {
public:
	constexpr SPMessageDecoder(const SPMessage &msg) :
			_msg(msg), _cursor(0) {
	}

	constexpr auto GetMessage() const {
		return _msg;
	}

	template<typename T,
			typename std::enable_if<std::is_unsigned<T>::value, int>::type = 0>
	auto decode(T *dest) {
		if (_msg.GetLen() - _cursor < sizeof(*dest)) {
			return -ENODATA;
		}

		const unsigned char *p = _msg.GetDataLocation() + _cursor;
		SPMessage::unpack_data(p, dest, sizeof(T));
		_cursor += sizeof(*dest);

		return 0;
	}

	template<typename T, typename uT = typename std::make_unsigned<T>::type,
			typename std::enable_if<std::is_signed<T>::value, int>::type = 0>
	auto decode(T *dest) {
		if (_msg.GetLen() - _cursor < sizeof(*dest)) {
			return -ENODATA;
		}

		const unsigned char *p = _msg.GetDataLocation() + _cursor;

		uT val;
		SPMessage::unpack_data(p, dest, sizeof(T));
		_cursor += sizeof(*dest);

		if (val <= std::numeric_limits<T>::max()) {
			*dest = val;
		} else {
			*dest = -1 - (T) (std::numeric_limits<uT>::max() - val);
		}
		return 0;
	}

private:
	const SPMessage &_msg;
	size_t _cursor;
};

class SPMessageEncoder {
public:
	constexpr SPMessageEncoder(SPMessage &msg) :
			_msg(msg), _cursor(0) {
	}

	constexpr SPMessage& GetMessage() const {
		return _msg;
	}

	template<typename T, typename std::enable_if<std::is_arithmetic<T>::value,
			int>::type = 0>
	auto encode(const T *data) {
		if (_msg.GetMaxLen() - _cursor < sizeof(*data)) {
			return -ENOMEM;
		}

		unsigned char *p = _msg.GetDataLocation() + _cursor;
		SPMessage::pack_data(p, data, sizeof(T));
		_cursor += sizeof(*data);

		return 0;
	}

	int write(const uint8_t *data, size_t len) {
		if (_msg.GetMaxLen() - _cursor < len) {
			return -ENOMEM;
		}

		_msg.write(_cursor, data, len);
		_cursor += len;

		return len;
	}

	constexpr size_t serializeSize() const {
		return _msg.GetHeaderSize() + _msg.GetLen() + _msg.GetFooterSize();
	}

	int serialize(uint8_t *dest, size_t len) {
		if(len < serializeSize())
			return -ENOMEM;

		unsigned char *p = dest;
		SPMessage::pack_data(p, &_msg.MAGIC[0], sizeof(_msg.MAGIC[0])); p += sizeof(_msg.MAGIC[0]);
		SPMessage::pack_data(p, &_msg.MAGIC[1], sizeof(_msg.MAGIC[1])); p += sizeof(_msg.MAGIC[1]);

		auto destId = _msg.GetDest();
		SPMessage::pack_data(p, &destId, sizeof(destId)); p += sizeof(destId);

		auto cmd = _msg.GetCommand();
		SPMessage::pack_data(p, &cmd, sizeof(cmd)); p += sizeof(cmd);

		auto handler = _msg.GetHandler();
		SPMessage::pack_data(p, &handler, sizeof(handler)); p += sizeof(handler);

		std::memcpy(p, _msg.GetDataLocation(), _msg.GetLen()); p += _msg.GetLen();

		auto crc = _msg.GetCrc();
		SPMessage::pack_data(p, &crc, sizeof(crc)); p += sizeof(crc);

		return p - dest;
	}

	void Close() {
		_msg.SetLen(_cursor);
		_msg.Close();
	}

private:
	SPMessage &_msg;
	size_t _cursor;
};

#endif /* INC_SPMESSAGE_HPP_ */
