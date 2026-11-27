package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.*;
public class ParcelActivity extends Activity {
    static final class Payload implements Parcelable {
        final String title;final long position;Payload(String t,long p){title=t;position=p;}public int describeContents(){return 0;}public void writeToParcel(Parcel out,int flags){out.writeString(title);out.writeLong(position);}
        public static final Creator<Payload> CREATOR=new Creator<Payload>(){public Payload createFromParcel(Parcel input){return new Payload(input.readString(),input.readLong());}public Payload[] newArray(int n){return new Payload[n];}};
    }
    protected void onCreate(Bundle state){super.onCreate(state);Parcelable original=new Payload("Original 📺",9876543210L);Parcel parcel=Parcel.obtain();original.writeToParcel(parcel,0);byte[] encoded=parcel.marshall();Parcel received=Parcel.obtain();received.unmarshall(encoded,0,encoded.length);received.setDataPosition(0);Payload value=Payload.CREATOR.createFromParcel(received);if(!value.title.equals("Original 📺")||value.position!=9876543210L||received.dataPosition()!=received.dataSize())throw new AssertionError("Original Parcelable payload");parcel.recycle();received.recycle();System.out.println("ORIGINAL_PARCELABLE_CREATOR_ROUNDTRIP_OK");}
}
