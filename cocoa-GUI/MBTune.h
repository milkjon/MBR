//
//  MBTune.h
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import <Cocoa/Cocoa.h>


@interface MBTune : NSObject {
	NSString *artist_;
	NSString *title_;
	NSString *album_;
	NSString *trackID_;
	NSString *duration_;
	NSString *genre_;
	
	int ID_;
	NSDate* requestTime_;
	NSString* requester_;
	NSString* dedication_;
}

-(NSString *) artist;
-(NSString *) title;
-(NSString *) album;
-(NSString *) genre;
-(NSString *) requester;
-(NSString *) dedication;
-(NSString *) duration;
-(NSString *) trackID;
-(NSDate *) requestTime;

-(void) setArtist: (NSString *) artist;
-(void) setTitle: (NSString *) title;
-(void) setAlbum: (NSString *) album;
-(void) setGenre: (NSString *) genre;
-(void) setRequester: (NSString *) requester;
-(void) setDedication: (NSString *) dedication;
-(void) setTrackID: (NSString *) trackID;
-(void) setDuration: (NSString *) length;
-(void) setRequestTime: (NSDate *) requestTime;

-(id) initWithXML: (NSXMLElement *) element;

@end
