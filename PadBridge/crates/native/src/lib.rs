//! Host JNI bridge. This is NOT a loader for Android/Bionic native libraries.
use jni::{
    objects::{JByteArray, JClass, JString, JValue},
    sys::{jint, jstring},
    JNIEnv,
};
use sdl2::{
    event::Event,
    image::{InitFlag, LoadTexture},
    keyboard::Keycode,
    pixels::Color,
    rect::Rect,
};
use serde::Serialize;
use std::sync::{Mutex, OnceLock};

#[derive(Clone, Default, Serialize)]
struct Node {
    kind: i32,
    text: String,
    children: Vec<usize>,
    #[serde(skip)]
    image: Vec<u8>,
    image_bytes: usize,
}
#[derive(Clone, Default, Serialize)]
struct Scene {
    nodes: Vec<Node>,
    root: usize,
    focus: usize,
}
static SCENE: OnceLock<Mutex<Scene>> = OnceLock::new();
fn scene() -> &'static Mutex<Scene> {
    SCENE.get_or_init(|| {
        Mutex::new(Scene {
            nodes: vec![Node::default()],
            ..Scene::default()
        })
    })
}
fn fail(env: &mut JNIEnv, message: impl ToString) {
    if !env.exception_check().unwrap_or(true) {
        let _ = env.throw_new(
            "java/lang/UnsupportedOperationException",
            message.to_string(),
        );
    }
}

#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_create(
    mut env: JNIEnv,
    _: JClass,
    kind: jint,
) -> jint {
    let mut s = scene().lock().unwrap();
    if s.nodes.len() >= 1000 || !(0..=3).contains(&kind) {
        fail(&mut env, "View type or count limit exceeded");
        return 0;
    }
    s.nodes.push(Node {
        kind,
        ..Node::default()
    });
    (s.nodes.len() - 1) as jint
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_text(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    text: JString,
) {
    match env.get_string(&text) {
        Ok(value) => {
            let value: String = value.into();
            if value.len() > 16384 {
                fail(&mut env, "Text exceeds limit");
                return;
            }
            if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
                n.text = value;
            } else {
                fail(&mut env, "Invalid view");
            }
        }
        Err(e) => fail(&mut env, e),
    }
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_image(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    bytes: JByteArray,
) {
    match env.convert_byte_array(&bytes) {
        Ok(value) => {
            if value.len() > 4 * 1024 * 1024 {
                fail(&mut env, "Image exceeds limit");
                return;
            }
            if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
                n.image_bytes = value.len();
                n.image = value;
            } else {
                fail(&mut env, "Invalid view");
            }
        }
        Err(e) => fail(&mut env, e),
    }
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_child(
    mut env: JNIEnv,
    _: JClass,
    parent: jint,
    child: jint,
) {
    let mut s = scene().lock().unwrap();
    if parent <= 0
        || child <= 0
        || parent == child
        || parent as usize >= s.nodes.len()
        || child as usize >= s.nodes.len()
    {
        fail(&mut env, "Invalid view hierarchy");
        return;
    }
    s.nodes[parent as usize].children.push(child as usize);
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_root(mut env: JNIEnv, _: JClass, id: jint) {
    let mut s = scene().lock().unwrap();
    if id <= 0 || id as usize >= s.nodes.len() {
        fail(&mut env, "Invalid root");
        return;
    }
    s.root = id as usize;
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_focus(_env: JNIEnv, _: JClass, id: jint) {
    scene().lock().unwrap().focus = id as usize;
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_snapshot(
    mut env: JNIEnv,
    _: JClass,
) -> jstring {
    let data = serde_json::to_string(&*scene().lock().unwrap()).unwrap();
    match env.new_string(data) {
        Ok(s) => s.into_raw(),
        Err(e) => {
            fail(&mut env, e);
            std::ptr::null_mut()
        }
    }
}
fn leaves(s: &Scene, id: usize, result: &mut Vec<usize>, depth: usize) -> Result<(), String> {
    if depth > 32 || result.len() > 1000 {
        return Err("View hierarchy exceeds limit or contains a cycle".into());
    }
    if let Some(node) = s.nodes.get(id) {
        if node.kind != 0 {
            result.push(id);
        }
        for child in &node.children {
            leaves(s, *child, result, depth + 1)?;
        }
    }
    Ok(())
}
fn key(key: Keycode) -> Option<i32> {
    match key {
        Keycode::Up => Some(19),
        Keycode::Down => Some(20),
        Keycode::Left => Some(21),
        Keycode::Right => Some(22),
        Keycode::Return | Keycode::Space => Some(23),
        _ => None,
    }
}
fn run(env: &mut JNIEnv) -> Result<(), String> {
    let sdl = sdl2::init()?;
    let video = sdl.video()?;
    let ttf = sdl2::ttf::init().map_err(|e| e.to_string())?;
    let _image = sdl2::image::init(InitFlag::PNG | InitFlag::JPG)?;
    let window = video
        .window("PadBridge • Android application", 1280, 720)
        .position_centered()
        .resizable()
        .build()
        .map_err(|e| e.to_string())?;
    let mut canvas = window
        .into_canvas()
        .software()
        .build()
        .map_err(|e| e.to_string())?;
    let texture_creator = canvas.texture_creator();
    let font = ttf.load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25)?;
    let mut events = sdl.event_pump()?;
    let mut targets: Vec<(usize, Rect)> = vec![];
    'running: loop {
        for event in events.poll_iter() {
            match event {
                Event::Quit { .. }
                | Event::KeyDown {
                    keycode: Some(Keycode::Escape),
                    ..
                } => break 'running,
                Event::KeyDown {
                    keycode: Some(k), ..
                } => {
                    if let Some(code) = key(k) {
                        env.call_static_method(
                            "org/padtv/bridge/Host",
                            "handleKey",
                            "(I)V",
                            &[JValue::Int(code)],
                        )
                        .map_err(|e| e.to_string())?;
                    }
                }
                Event::MouseButtonDown {
                    x,
                    y,
                    mouse_btn: sdl2::mouse::MouseButton::Left,
                    ..
                } => {
                    if let Some((id, _)) = targets.iter().find(|(_, r)| r.contains_point((x, y))) {
                        env.call_static_method(
                            "org/padtv/bridge/Host",
                            "click",
                            "(I)V",
                            &[JValue::Int(*id as i32)],
                        )
                        .map_err(|e| e.to_string())?;
                    }
                }
                _ => {}
            }
        }
        let state = scene().lock().unwrap().clone();
        let mut items = vec![];
        leaves(&state, state.root, &mut items, 0)?;
        let (width, _) = canvas.output_size()?;
        let mut y = 36;
        targets.clear();
        canvas.set_draw_color(Color::RGB(13, 28, 29));
        canvas.clear();
        for id in items {
            let node = &state.nodes[id];
            let height = if node.kind == 3 { 180 } else { 70 };
            let area = Rect::new(40, y, width.saturating_sub(80).max(1), height);
            if node.kind == 2 {
                canvas.set_draw_color(if id == state.focus {
                    Color::RGB(88, 57, 180)
                } else {
                    Color::RGB(32, 65, 65)
                });
                canvas.fill_rect(area)?;
                targets.push((id, area));
            }
            if node.kind == 3 && !node.image.is_empty() {
                let texture = texture_creator.load_texture_bytes(&node.image)?;
                let q = texture.query();
                let scale = (180.0 / q.height as f64).min(area.width() as f64 / q.width as f64);
                canvas.copy(
                    &texture,
                    None,
                    Rect::new(
                        50,
                        y,
                        (q.width as f64 * scale) as u32,
                        (q.height as f64 * scale) as u32,
                    ),
                )?;
            } else if !node.text.is_empty() {
                let surface = font
                    .render(&node.text)
                    .blended_wrapped(Color::RGB(239, 247, 244), area.width().saturating_sub(24))
                    .map_err(|e| e.to_string())?;
                let texture = texture_creator
                    .create_texture_from_surface(&surface)
                    .map_err(|e| e.to_string())?;
                canvas.copy(
                    &texture,
                    None,
                    Rect::new(54, y + 14, surface.width(), surface.height()),
                )?;
            }
            y += height as i32 + 14;
        }
        canvas.present();
        std::thread::sleep(std::time::Duration::from_millis(16));
    }
    Ok(())
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_run(mut env: JNIEnv, _: JClass) {
    if let Err(e) = run(&mut env) {
        fail(&mut env, e);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn dpad_mapping() {
        assert_eq!(key(Keycode::Down), Some(20));
        assert_eq!(key(Keycode::Return), Some(23));
        assert_eq!(key(Keycode::A), None);
    }
    #[test]
    fn hierarchy_cycle_rejected() {
        let s = Scene {
            nodes: vec![Node {
                children: vec![0],
                ..Node::default()
            }],
            ..Scene::default()
        };
        assert!(leaves(&s, 0, &mut vec![], 0).is_err());
    }
}
