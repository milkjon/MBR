tell application "iTunes"
	set pl to current playlist
	set cid to id of current track
	set i to 1
	repeat with t in tracks of pl
		set i to i + 1
		if id of t = cid then
			exit repeat
		end if
	end repeat
	
	set e to i + 4
	if e > (count of tracks of pl) then
		set e to count of tracks of pl
	end if
	get items i thru e of (get name of tracks of pl)
end tell