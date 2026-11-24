package org.padtv.kotlinprobe
import android.app.Activity
import android.os.Bundle
import android.widget.Button
class KotlinActivity : Activity() {
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val button = Button(this)
        val numbers = listOf(7, 14, 21)
        val total = numbers.sum()
        check(total == 42)
        button.text = "Kotlin DEX executed: $total"
        button.setOnClickListener { button.text = "KOTLIN_DPAD_OK"; android.util.Log.i("KOTLIN", "KOTLIN_DPAD_OK") }
        setContentView(button)
        android.util.Log.i("KOTLIN", "KOTLIN_ORIGINAL_DEX_OK")
    }
}
