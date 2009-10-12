//
//  MBRiTunes.h
//  MBR
//
//  Created by Jonathan on 10/10/09.
//

#import <Cocoa/Cocoa.h>


@interface MBiTunes : NSObject
{
	NSString *currentlyPlayingScript_;
	NSString *nextTracksScript_;
	NSString *playlistsScript_;
	NSString *addToiTunesScriptTemplate_;
}

- (NSString *) currentlyPlaying;
- (NSArray *) nextFive; 
- (NSArray *) playlists;

- (void) addID: (NSString *)id toPlaylist: (NSString *)playlist;

@end