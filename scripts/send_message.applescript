on run argv
	if (count of argv) is less than 3 then error "Expected sms_url, compose_delay, post_send_delay"

	set smsUrl to item 1 of argv
	set composeDelay to (item 2 of argv) as real
	set postSendDelay to (item 3 of argv) as real

	open location (smsUrl)
	repeat 20 times
		tell application "System Events"
			if exists process "Messages" then
				tell process "Messages"
					if (count of windows) is greater than 0 then exit repeat
				end tell
			end if
		end tell
		delay 0.15
	end repeat

	delay composeDelay

	tell application "Messages" to activate
	delay 0.4

	tell application "System Events"
		tell process "Messages"
			set frontWindow to front window

			try
				if exists button "보내기" of frontWindow then
					click button "보내기" of frontWindow
					return "clicked:ko"
				else if exists button "Send" of frontWindow then
					click button "Send" of frontWindow
					return "clicked:en"
				else
					key code 36
					return "key:return"
				end if
			on error
				key code 36
				return "fallback:return"
			end try
		end tell
	end tell

	delay postSendDelay
end run
