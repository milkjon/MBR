//
//  UntitledAppDelegate.h
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import <Cocoa/Cocoa.h>
#import "MBiTunes.h"

@interface MBRAppDelegate : NSObject {
	NSMutableArray *requests;
	NSTimer *requestCheckTimer_;
	NSTimer *songQueryTimer_;
	
	MBiTunes *iTunes_;

	IBOutlet NSArrayController *arrayController;
	IBOutlet NSTableView *tableView;
}
- (IBAction) addToiTunesPlaylist: (id) sender;
- (IBAction) getNextSongs: (id) sender;

@end
