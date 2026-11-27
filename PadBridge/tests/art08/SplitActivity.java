package org.padtv.artprobe;
public final class SplitActivity extends android.app.Activity {
    protected void onCreate(android.os.Bundle state){super.onCreate(state);if(Secondary.answer()!=42)throw new AssertionError("Feature DEX was not executed");android.widget.TextView view=new android.widget.TextView(this);view.setText("ORIGINAL_ART_FEATURE_DEX_42");setContentView(view);System.out.println("ORIGINAL_ART_FEATURE_DEX_42");}
}
