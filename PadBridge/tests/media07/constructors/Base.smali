.class public Lorg/padtv/ctors/Base;
.super Ljava/lang/Object;
.field public static calls:I
.field public value:I
.method public constructor <init>(I)V
 .registers 4
 invoke-direct {p0}, Ljava/lang/Object;-><init>()V
 iput p1, p0, Lorg/padtv/ctors/Base;->value:I
 sget v0, Lorg/padtv/ctors/Base;->calls:I
 add-int/lit8 v0, v0, 0x1
 sput v0, Lorg/padtv/ctors/Base;->calls:I
 return-void
.end method
