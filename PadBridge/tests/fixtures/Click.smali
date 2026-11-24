.class public Lorg/padtv/fixture/Click;
.super Ljava/lang/Object;
.implements Landroid/view/View$OnClickListener;
.field private text:Landroid/widget/TextView;
.method public constructor <init>(Landroid/widget/TextView;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1,p0,Lorg/padtv/fixture/Click;->text:Landroid/widget/TextView;
    return-void
.end method
.method public onClick(Landroid/view/View;)V
    .locals 2
    iget-object v0,p0,Lorg/padtv/fixture/Click;->text:Landroid/widget/TextView;
    const-string v1, "DPAD_CLICK_OK"
    invoke-virtual {v0,v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    return-void
.end method
