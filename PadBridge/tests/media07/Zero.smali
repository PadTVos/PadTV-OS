.class public Lorg/padtv/zero/Zero;
.super Landroid/app/Activity;
.field static attempts:I
.method public constructor <init>()V
 .locals 0
 invoke-direct {p0}, Landroid/app/Activity;-><init>()V
 return-void
.end method
.method public static retry()I
 .locals 2
 :entry
 sget v0, Lorg/padtv/zero/Zero;->attempts:I
 add-int/lit8 v0,v0,1
 sput v0, Lorg/padtv/zero/Zero;->attempts:I
 const/4 v1,2
 if-ge v0,v1,:done
 :start
 new-instance v1, Ljava/lang/IllegalStateException;
 invoke-direct {v1}, Ljava/lang/IllegalStateException;-><init>()V
 throw v1
 :end
 .catch Ljava/lang/IllegalStateException; {:start .. :end} :entry
 :done
 return v0
.end method
.method protected onCreate(Landroid/os/Bundle;)V
 .locals 2
 invoke-static {}, Lorg/padtv/zero/Zero;->retry()I
 move-result v0
 const/4 v1,2
 if-eq v0,v1,:success
 new-instance v0, Ljava/lang/AssertionError;
 invoke-direct {v0}, Ljava/lang/AssertionError;-><init>()V
 throw v0
 :success
 sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;
 const-string v1,"DEX_ZERO_HANDLER_OK"
 invoke-virtual {v0,v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
 return-void
.end method
