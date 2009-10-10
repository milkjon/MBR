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

	NSTask *serverTask_;
	
	IBOutlet NSArrayController *arrayController;
	IBOutlet NSTableView *tableView;
}
- (IBAction) addToiTunesPlaylist: (id) sender;
- (IBAction) getNextSongs: (id) sender;
- (IBAction) startServer: (id) sender;
- (IBAction) stopServer: (id) sender;

@end
