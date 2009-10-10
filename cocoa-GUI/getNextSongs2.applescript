on minimum(a, b)
	if a < b then
		return a
	else
		return b
	end if
end minimum

tell application "iTunes"
	set _playlist to current playlist
	set _id to id of current track
	set i to 1
	-- Does the index really need to be determined like this?
	repeat with t in tracks of _playlist
		set i to i + 1
		if _id = id of t then
			exit repeat
		end if
	end repeat
	set c to count of tracks of _playlist
end tell
set _last to minimum(i + 4, c)
tell application "iTunes" to get items i thru _last of (get name of tracks of _playlist)