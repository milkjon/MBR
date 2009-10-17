//
//  MBRiTunes.m
//  MBR
//
//  Created by Jonathan on 10/10/09.
//

#import "MBiTunes.h"

@implementation MBiTunes

- (NSString *) _runAppleScript: (NSString *) source
{
	NSAppleScript *script = [[[NSAppleScript alloc] initWithSource: source] autorelease];
	NSDictionary *err=nil;
	NSString *result = [[script executeAndReturnError: &err] stringValue];
	if (err) return [NSString stringWithFormat: @"ERROR!!!, %@", err];
	return result;
}

#pragma mark -

- (NSString *) currentlyPlaying
{
	NSString *result = [self _runAppleScript: currentlyPlayingScript_];
	return result;
}

- (NSArray *) nextFive
{
	NSString *upcoming = [self _runAppleScript: nextTracksScript_];
	if ([upcoming hasPrefix: @"ERROR!!!"])
		return nil;

	NSArray *songList = [upcoming componentsSeparatedByString: @"\r"];
	return songList;
}

- (NSArray *) playlists
{
	NSString *playlists = [self _runAppleScript: playlistsScript_];
	NSArray *lists = [playlists componentsSeparatedByString: @"\r"];
	return lists;	
}

- (void) addID: (NSString *)trackID toPlaylist: (NSString *)playlist
{
	NSString *source = [NSString stringWithFormat: addToiTunesScriptTemplate_, trackID, playlist]; 
	[self _runAppleScript: source];
}

#pragma mark -

- (id) init
{
	self = [super init];
	if (self != nil) {
		currentlyPlayingScript_ = [[NSString alloc] initWithContentsOfFile: 
			[[NSBundle mainBundle] pathForResource:@"getCurrentTrack" ofType:@"applescript"]];
		nextTracksScript_ = [[NSString alloc] initWithContentsOfFile:
			[[NSBundle mainBundle] pathForResource:@"getNextSongs" ofType:@"applescript"]];
		addToiTunesScriptTemplate_ = [[NSString alloc] initWithContentsOfFile:
			[[NSBundle mainBundle] pathForResource:@"addToiTunes" ofType:@"applescript"]];
		playlistsScript_ = [[NSString alloc] initWithContentsOfFile:
			[[NSBundle mainBundle] pathForResource:@"getPlaylists" ofType:@"applescript"]];
	}
	return self;
}

- (void) dealloc
{
	[currentlyPlayingScript_ release];
	[nextTracksScript_ release];
	[addToiTunesScriptTemplate_ release];
	[playlistsScript_ release];
	[super dealloc];
}
@end

