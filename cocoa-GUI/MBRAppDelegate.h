//
//  UntitledAppDelegate.h
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import <Cocoa/Cocoa.h>

@interface MBRAppDelegate : NSObject {
	NSMutableArray *requests;
	NSTimer *requestCheckTimer_;
	NSTimer *songQueryTimer_;
	

	IBOutlet NSArrayController *arrayController;
	IBOutlet NSTableView *tableView;
}
- (IBAction) add: (id) sender;
- (IBAction) addToiTunesPlaylist: (id) sender;
- (IBAction) getNextSongs: (id) sender;

@end
