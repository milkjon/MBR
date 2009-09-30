//
//  MBTune.h
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import <Cocoa/Cocoa.h>


@interface MBTune : NSObject {
	NSString* artist_;
	NSString* title_;
	NSString* trackID_;
	NSString* length_;
	NSString* path_;
	
	NSDate* requestTime_;
	NSString* requester_;
	NSString* dedication_;
}

-(NSString*) artist;
-(NSString*) path;
-(NSString*) title;
-(NSString*) requester;
-(NSString*) dedication;
-(NSString*) trackID;
-(NSString*) length;
-(NSDate*) requestTime;

-(void) setArtist: (NSString*) artist;
-(void) setPath: (NSString*) path;
-(void) setTitle: (NSString*) title;
-(void) setRequester: (NSString*) requester;
-(void) setDedication: (NSString*) dedication;
-(void) setTrackID: (NSString*) trackID;
-(void) setLength: (NSString*) length;
-(void) setRequestTime: (NSDate*) requestTime;
@end
