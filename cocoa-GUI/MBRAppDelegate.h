//
//  UntitledAppDelegate.h
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import <Cocoa/Cocoa.h>

@interface MBRAppDelegate : NSObject {
	NSMutableArray *requests;
	NSTimer *timer_;
	
	IBOutlet NSArrayController *arrayController;
	IBOutlet NSTableView *tableView;
}
- (IBAction) add: (id) sender;
- (IBAction) addToiTunesPlaylist: (id) sender;

@end
