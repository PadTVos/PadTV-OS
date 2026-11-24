.class public Lorg/padtv/fixture/Main;
.super Landroid/app/Activity;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 8
    invoke-super {p0,p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
    # Real DEX arithmetic and conditional control flow, not a precomputed UI.
    const/4 v0, 0x6
    const/4 v1, 0x7
    mul-int v2, v0, v1
    const/16 v3, 0x2a
    if-ne v2,v3,:failure
    invoke-static {v2}, Ljava/lang/Integer;->toString(I)Ljava/lang/String;
    move-result-object v2
    const-string v0, "result.txt"
    const/4 v1, 0
    invoke-virtual {p0,v0,v1}, Landroid/content/Context;->openFileOutput(Ljava/lang/String;I)Ljava/io/FileOutputStream;
    move-result-object v0
    invoke-virtual {v2}, Ljava/lang/String;->getBytes()[B
    move-result-object v1
    invoke-virtual {v0,v1}, Ljava/io/FileOutputStream;->write([B)V
    invoke-virtual {v0}, Ljava/io/FileOutputStream;->close()V
    new-instance v4, Landroid/widget/LinearLayout;
    invoke-direct {v4,p0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V
    const/4 v0, 1
    invoke-virtual {v4,v0}, Landroid/widget/LinearLayout;->setOrientation(I)V
    new-instance v5, Landroid/widget/TextView;
    invoke-direct {v5,p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    const-string v0, "PadBridge / original APK / DEX 6 x 7 = 42"
    invoke-virtual {v5,v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    invoke-virtual {v4,v5}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
    new-instance v6, Landroid/widget/ImageView;
    invoke-direct {v6,p0}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V
    invoke-virtual {p0}, Landroid/content/Context;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v0
    const-string v1, "test.png"
    invoke-virtual {v0,v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v0
    invoke-static {v0}, Landroid/graphics/BitmapFactory;->decodeStream(Ljava/io/InputStream;)Landroid/graphics/Bitmap;
    move-result-object v1
    invoke-virtual {v0}, Ljava/io/InputStream;->close()V
    invoke-virtual {v6,v1}, Landroid/widget/ImageView;->setImageBitmap(Landroid/graphics/Bitmap;)V
    invoke-virtual {v4,v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
    new-instance v6, Landroid/widget/Button;
    invoke-direct {v6,p0}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V
    const-string v0, "Select with Enter / TV remote"
    invoke-virtual {v6,v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    new-instance v7, Lorg/padtv/fixture/Click;
    invoke-direct {v7,v5}, Lorg/padtv/fixture/Click;-><init>(Landroid/widget/TextView;)V
    invoke-virtual {v6,v7}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V
    invoke-virtual {v4,v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
    invoke-virtual {p0,v4}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V
    const-string v0, "PadBridgeFixture"
    const-string v1, "DEX_ACTIVITY_STORAGE_OK"
    invoke-static {v0,v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    return-void
    :failure
    new-instance v0, Ljava/lang/IllegalStateException;
    const-string v1, "DEX arithmetic failed"
    invoke-direct {v0,v1}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V
    throw v0
.end method
