/*
 * DgbLog.hpp
 *
 *  Created on: May 14, 2021
 *      Author: Vlad
 */

#ifndef INC_DGBLOG_HPP_
#define INC_DGBLOG_HPP_

#include <string>
#include <cstdio>
#include <cstdarg>
#include "error.h"
#include "main.h"

#define FILENAME_WE "test"
#define VT100_INF
#define VT100_WRN
#define VT100_ERR
#define VT100_DBG
#define VT100_RESET

/**
 *	@brief Log class
 */
class DgbLog
{
public:
	/**
	 * @brief Log level
	 *
	 */
    enum class log_level
    {
        NONE = 0x00,/**< NONE */
        ERR,        /**< Error */
        WRN,        /**< Warning */
        INF,        /**< Information */
        DBG         /**< Debug */
    };

private:
    static inline const enum log_level _defaultLogLevel = log_level::INF; ///< Default log level.
    static inline char msg_buff[100]; ///< Buffer used to format message.
    static inline char result[100]; ///< Buffer used to store the whole line.

    const std::string_view _name; ///< Module name.
    const log_level _level; ///< Log level.
public:

    /**
     * @brief Declare a log instance
     *
     * @param name module name
     * @param level log level
     */
	constexpr DgbLog(const std::string_view &name = FILENAME_WE, log_level level = _defaultLogLevel): _name(std::move(name)), _level(level)
    {};

private:

	/**
	 * @brief Get template format
	 *
	 * @param level log level
	 * @return template format
	 */
    static constexpr const std::string_view GetFormatString(log_level level)
    {
        switch(level) {
            case log_level::INF:
                return std::string_view(VT100_INF "i [%s] %s" VT100_RESET "\r\n");
                break;
            case log_level::WRN:
                return std::string_view(VT100_WRN "w [%s] %s" VT100_RESET "\r\n");
                break;
            case log_level::ERR:
                return std::string_view(VT100_ERR "e [%s] %s" VT100_RESET "\r\n");
                break;
            case log_level::DBG:
                return std::string_view(VT100_DBG "d [%s] %s" VT100_RESET "\r\n");
                break;
            case log_level::NONE:
            default:
                return std::string_view();
        }
    }

public:
    /**
	 * @brief Log an entry
     *
     * @param level entry level
     * @param fmt format string
     */
    void LogEntry(log_level level, const char *fmt, ...) const
    {
        int len = 0;
        va_list args;
        va_start(args, fmt);
        vsprintf(msg_buff, fmt, args);
        va_end(args);

        len = snprintf(result, sizeof(result), DgbLog::GetFormatString(level).data(), _name.data(), msg_buff);
        printf("%d %s", len, result);
    }

    /**
	 * @brief Get module log level
     *
     * @return
     */
    constexpr const log_level GetLogLevel() const { return _level; }
};

/**
 * @brief Prints a error level message
 *
 */
#define LOG_ERR(desc, ...)  do{ if(Logger.GetLogLevel() >= DgbLog::log_level::ERR)  Logger.LogEntry(DgbLog::log_level::ERR,  desc, ##__VA_ARGS__); }while(0);

/**
 * @brief Prints a warning level message
 *
 */
#define LOG_WRN(desc, ...)  do{ if(Logger.GetLogLevel() >= DgbLog::log_level::WRN) Logger.LogEntry(DgbLog::log_level::WRN, desc, ##__VA_ARGS__); }while(0);

/**
 * @brief Prints an information level message
 *
 */
#define LOG_INF(desc, ...)  do{ if(Logger.GetLogLevel() >= DgbLog::log_level::INF) Logger.LogEntry(DgbLog::log_level::INF, desc, ##__VA_ARGS__); }while(0);

/**
 * @brief Prints a debug level message
 *
 */
#define LOG_DBG(desc, ...)  do{ if(Logger.GetLogLevel() >= DgbLog::log_level::DBG)  Logger.LogEntry(DgbLog::log_level::DBG, desc, ##__VA_ARGS__); }while(0);

/**
 * @brief Prints a message without a level.
 *
 */
#define LOG_RAW(desc, ...)  do{ if(Logger.GetLogLevel() >= DgbLog::log_level::NONE) _lograw(desc, ##__VA_ARGS__);}while(0);

/**
 * \def IS_DEBUGGER_CONNECTED()
 * @brief Checks if a debugger is connected
 *
 */
#define IS_DEBUGGER_CONNECTED()   \
    ((CoreDebug->DHCSR & CoreDebug_DHCSR_C_DEBUGEN_Msk) == CoreDebug_DHCSR_C_DEBUGEN_Msk)

/**
 * \def TRIGGER_BKPT()
 * @brief Triggers a breakpoint stop when debugger is connected
 *
 */
#define TRIGGER_BKPT()																					\
do {                                                                                                    \
	if (IS_DEBUGGER_CONNECTED()) __BKPT(0);  \
} while(0)

/**
 * \def ERR_FATAL_TRAP(ERROR_CODE, ERROR_MSG)
 * @brief Logs, triggers a breakpoint stop and triggers
 * a fatal_oops() when ERROR_CODE has a negative value
 *
 */
#define ERR_FATAL_TRAP(ERROR_CODE, ERROR_MSG)                                                               \
do {                                                                                                        \
    if (ERROR_CODE < 0)                                                                                     \
    {                                                                                                       \
        LOG_ERR("%s: " #ERROR_MSG " %d", __func__ , ERROR_CODE);                                		    \
        TRIGGER_BKPT();																						\
        assert_param(0);                                                                                    \
    }                                                                                                       \
} while(0)

/**
 * \def RETURN_ON_ERROR(ERROR_CODE, ERROR_MSG)
 * @brief Logs, triggers a breakpoint stop and returns the
 * ERROR_CODE when ERROR_CODE has a negative value
 *
 */
#define RETURN_ON_ERROR(ERROR_CODE, ERROR_MSG)                                                              \
do {                                                                                                        \
    if (ERROR_CODE < 0)                                                                                     \
    {                                                                                                       \
        LOG_ERR("%s: " #ERROR_MSG " %d", __func__ , ERROR_CODE);                                			\
        TRIGGER_BKPT();																						\
        return ERROR_CODE;                                                                                  \
    }                                                                                                       \
} while(0)

/**
 * \def RETURN_ON_ERROR_NO_BKPT(ERROR_CODE, ERROR_MSG)
 * @brief Logs and returns the
 * ERROR_CODE when ERROR_CODE has a negative value
 *
 */
#define RETURN_ON_ERROR_NO_BKPT(ERROR_CODE, ERROR_MSG)                                                      \
do {                                                                                                        \
    if (ERROR_CODE < 0)                                                                                     \
    {                                                                                                       \
        LOG_ERR("%s: " #ERROR_MSG " %d", __func__, ERROR_CODE);                               				\
        return ERROR_CODE;                                                                                  \
    }                                                                                                       \
} while(0)

/**
 * \def GOTO_ON_ERROR(ERROR_CODE, ERROR_MSG, LABEL)
 * @brief Logs, triggers a breakpoint stop and returns the
 * ERROR_CODE when ERROR_CODE has a negative value
 *
 */
#define GOTO_ON_ERROR(ERROR_CODE, ERROR_MSG, LABEL)                                                   		\
do {                                                                                                        \
    if (ERROR_CODE < 0)                                                                                     \
    {                                                                                                       \
        LOG_ERR("%s: " #ERROR_MSG " %d", __func__ , ERROR_CODE);                                			\
        TRIGGER_BKPT();                                                                           			\
        goto LABEL;                                                                                         \
    }                                                                                                       \
} while(0)

/**
 * \def BREAK_ON_ERROR(ERROR_CODE, ERROR_MSG)
 * @brief Logs, triggers a breakpoint stop and breaks the loop/switch
 *  when when ERROR_CODE has a negative value
 *
 */
#define BREAK_ON_ERROR(ERROR_CODE, ERROR_MSG)                                                           \
if (ERROR_CODE < 0)                                                                                     \
{                                                                                                       \
	LOG_ERR("%s: " #ERROR_MSG " %d", __func__, ERROR_CODE);                                				\
	TRIGGER_BKPT();																						\
    break;                                                                                              \
}

/**
 * \def RETURN_ON_NULL_POINTER(PTR, ERROR_CODE, ERROR_MSG)
 * @brief Logs, triggers a breakpoint stop and returns the
 * ERROR_CODE when PTR is NULL
 *
 */
#define RETURN_ON_NULL_POINTER(PTR, ERROR_CODE, ERROR_MSG)                                             		\
do {                                                                                                        \
    if (PTR == NULL)                                                                                     	\
    {                                                                                                       \
        LOG_ERR("%s: " #ERROR_MSG " %d", __func__, ERROR_CODE);                                				\
        TRIGGER_BKPT();																						\
        return ERROR_CODE;                                                                                  \
    }                                                                                                       \
} while(0)

/**
 * \def RETURN_ON_NULL_PARAM(param)
 * @brief Check if the input pointer is NULL, if so it returns -EINVAL
 *
 */
#define RETURN_ON_NULL_PARAM(param) APP_NULL_PARAM_RETURN_CODE(param, -EINVAL)

/**
 * \def RETURN_VOID_ON_NULL_PARAM(param)
 * @brief Check if the input pointer is NULL, if so it returns -EINVAL
 *
 */
#define RETURN_VOID_ON_NULL_PARAM(param) APP_NULL_PARAM_RETURN_CODE(param, APP_DEBUG_NOTHING)

/**
 * \def STATIC_ASSERT(EXPR, MSG)
 * @brief Static assert
 *
 */
#define STATIC_ASSERT(EXPR, MSG)    _Static_assert(EXPR, MSG)

/**
 * \def APP_DEBUG_NOTHING
 * @brief Empty define used internally
 *
 */
#define APP_DEBUG_NOTHING

#endif /* INC_DGBLOG_HPP_ */
