package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.Bundle;import android.media.tv.TvContentRating;
public class RatingActivity extends Activity {
    protected void onCreate(Bundle state){super.onCreate(state);
        TvContentRating rating=TvContentRating.createRating("org.example","TV","PG","V","L");
        if(!TvContentRating.unflattenFromString(rating.flattenToString()).equals(rating))throw new AssertionError("Rating round trip");
        if(!rating.contains(TvContentRating.createRating("org.example","TV","PG","V")))throw new AssertionError("Subrating contains");
        if(rating.contains(TvContentRating.createRating("org.other","TV","PG","V")))throw new AssertionError("Domain isolation");
        try{TvContentRating.createRating("","TV","PG");throw new AssertionError("Empty domain");}catch(IllegalArgumentException expected){}
        try{TvContentRating.unflattenFromString("invalid");throw new AssertionError("Malformed rating");}catch(IllegalArgumentException expected){}
        System.out.println("ORIGINAL_AOSP_TV_RATING_ROUNDTRIP_CONTAINS_OK");
    }
}
