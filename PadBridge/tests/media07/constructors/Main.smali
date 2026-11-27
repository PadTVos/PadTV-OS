.class public Lorg/padtv/ctors/Main;
.super Landroid/app/Activity;
.method public constructor <init>()V
 .registers 1
 invoke-direct {p0}, Landroid/app/Activity;-><init>()V
 return-void
.end method
.method public onCreate(Landroid/os/Bundle;)V
 .registers 6
 invoke-super {p0,p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
 new-instance v0, Lorg/padtv/ctors/Child;
 const/16 v1, 0x2a
 invoke-direct {v0,v1}, Lorg/padtv/ctors/Base;-><init>(I)V
 iget v2, v0, Lorg/padtv/ctors/Base;->value:I
 if-ne v1,v2, :fail
 sget v2, Lorg/padtv/ctors/Base;->calls:I
 const/4 v1, 0x1
 if-ne v1,v2, :fail
 invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;
 move-result-object v2
 const-class v1, Lorg/padtv/ctors/Child;
 if-ne v1,v2, :fail
 sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;
 const-string v1, "DEX_CONSTRUCTOR_CLASS_ARGUMENT_SIDE_EFFECT_OK"
 invoke-virtual {v0,v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
 return-void
 :fail
 new-instance v0, Ljava/lang/AssertionError;
 invoke-direct {v0}, Ljava/lang/AssertionError;-><init>()V
 throw v0
.end method
