//! Host JNI bridge. This is NOT a loader for Android/Bionic native libraries.
use jni::{
    objects::{JByteArray, JClass, JString, JValue},
    sys::{jint, jintArray, jstring},
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
    visibility: i32,
    #[serde(skip)]
    image_version: u64,
    kind: i32,
    layout: i32,
    width: i32,
    height: i32,
    margin: [i32; 4],
    padding: [i32; 4],
    scroll: [i32; 2],
    text: String,
    children: Vec<usize>,
    #[serde(skip)]
    image: Vec<u8>,
    image_bytes: usize,
}
#[derive(Clone, Default, Serialize)]
struct Scene {
    window_flags: i32,
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
pub extern "system" fn Java_org_padtv_bridge_Native_visibility(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    value: jint,
) {
    if ![0, 4, 8].contains(&value) {
        fail(&mut env, "Invalid visibility");
        return;
    }
    if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
        n.visibility = value;
    } else {
        fail(&mut env, "Invalid view");
    }
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_windowFlags(
    mut env: JNIEnv,
    _: JClass,
    flags: jint,
) {
    if flags & !(1024 | 128) != 0 {
        fail(&mut env, "Unsupported window flags");
        return;
    }
    scene().lock().unwrap().window_flags = flags;
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_displaySize(
    mut env: JNIEnv,
    _: JClass,
) -> jintArray {
    let size = sdl2::init()
        .and_then(|s| s.video())
        .and_then(|v| v.desktop_display_mode(0));
    let (w, h) = if std::env::var("PADBRIDGE_HEADLESS").as_deref() == Ok("1") {
        (1280, 720)
    } else {
        match size {
            Ok(m) => (m.w, m.h),
            Err(e) => {
                fail(&mut env, e);
                return std::ptr::null_mut();
            }
        }
    };
    match env.new_int_array(2).and_then(|a| {
        env.set_int_array_region(&a, 0, &[w, h])?;
        Ok(a)
    }) {
        Ok(a) => a.into_raw(),
        Err(e) => {
            fail(&mut env, e);
            std::ptr::null_mut()
        }
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
        layout: 1,
        width: -2,
        height: -2,
        ..Node::default()
    });
    (s.nodes.len() - 1) as jint
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_layout(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    layout: jint,
) {
    if !(0..=2).contains(&layout) {
        fail(&mut env, "Unsupported layout mode");
        return;
    }
    if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
        n.layout = layout;
    } else {
        fail(&mut env, "Invalid view");
    }
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_size(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    width: jint,
    height: jint,
) {
    if !(-2..=16384).contains(&width) || !(-2..=16384).contains(&height) {
        fail(&mut env, "Invalid view dimensions");
        return;
    }
    if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
        n.width = width;
        n.height = height;
    } else {
        fail(&mut env, "Invalid view");
    }
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_scroll(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    x: jint,
    y: jint,
) {
    if !(-16384..=16384).contains(&x) || !(-16384..=16384).contains(&y) {
        fail(&mut env, "Scroll offset exceeds bounds");
        return;
    }
    if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
        n.scroll = [x, y];
    } else {
        fail(&mut env, "Invalid view");
    }
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_insets(
    mut env: JNIEnv,
    _: JClass,
    id: jint,
    padding: jni::sys::jboolean,
    left: jint,
    top: jint,
    right: jint,
    bottom: jint,
) {
    let values = [left, top, right, bottom];
    if values.iter().any(|v| !(-16384..=16384).contains(v)) {
        fail(&mut env, "View insets exceed bounds");
        return;
    }
    if let Some(n) = scene().lock().unwrap().nodes.get_mut(id as usize) {
        if padding != 0 {
            n.padding = values;
        } else {
            n.margin = values;
        }
    } else {
        fail(&mut env, "Invalid view");
    }
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
                n.image_version = n.image_version.wrapping_add(1);
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
#[cfg(test)]
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
        Keycode::Escape | Keycode::Backspace => Some(4),
        Keycode::F10 | Keycode::Application => Some(82),
        _ => None,
    }
}
fn measure(s: &Scene, id: usize, horizontal: bool, depth: usize) -> Result<u32, String> {
    if depth > 32 {
        return Err("Layout cycle or nesting limit".into());
    }
    let n = s.nodes.get(id).ok_or("Invalid layout node")?;
    if n.visibility == 8 {
        return Ok(0);
    }
    let explicit = if horizontal { n.width } else { n.height };
    if explicit >= 0 {
        return Ok(explicit as u32);
    }
    if n.kind != 0 {
        return Ok(if horizontal {
            240
        } else if n.kind == 3 {
            180
        } else {
            70
        });
    }
    let mut size = 0u32;
    for child in &n.children {
        let value = measure(s, *child, horizontal, depth + 1)?;
        if (horizontal && n.layout == 0) || (!horizontal && n.layout == 1) {
            size = size.saturating_add(value + 14);
        } else {
            size = size.max(value);
        }
    }
    Ok(size.min(16384))
}
fn arrange(
    s: &Scene,
    id: usize,
    area: Rect,
    result: &mut Vec<(usize, Rect)>,
    depth: usize,
) -> Result<(), String> {
    if depth > 32 || result.len() > 1000 {
        return Err("Layout cycle or view limit".into());
    }
    let n = s.nodes.get(id).ok_or("Invalid layout node")?;
    if n.visibility != 0 {
        return Ok(());
    }
    result.push((id, area));
    let area = Rect::new(
        area.x() + n.padding[0],
        area.y() + n.padding[1],
        area.width()
            .saturating_sub((n.padding[0] + n.padding[2]).max(0) as u32)
            .max(1),
        area.height()
            .saturating_sub((n.padding[1] + n.padding[3]).max(0) as u32)
            .max(1),
    );
    let horizontal = n.layout == 0;
    let available = if horizontal {
        area.width()
    } else {
        area.height()
    };
    let mut fixed = 0;
    let mut fill = 0;
    for child in &n.children {
        let c = &s.nodes[*child];
        if c.visibility == 8 {
            continue;
        }
        let length = if horizontal { c.width } else { c.height };
        fixed += (if horizontal {
            c.margin[0] + c.margin[2]
        } else {
            c.margin[1] + c.margin[3]
        })
        .max(0) as u32;
        if length == -1 {
            fill += 1;
        } else {
            fixed += measure(s, *child, horizontal, depth + 1)? + 14;
        }
    }
    let shared = available.saturating_sub(fixed) / fill.max(1);
    let mut offset = 0i32;
    for child in &n.children {
        let c = &s.nodes[*child];
        if c.visibility == 8 {
            continue;
        }
        let dimension = |length: i32, available: u32, natural: u32| {
            if length >= 0 {
                length as u32
            } else if length == -1 {
                available
            } else {
                natural.min(available)
            }
        };
        let width = dimension(
            c.width,
            if horizontal && n.layout != 2 && c.width == -1 {
                shared.max(1)
            } else {
                area.width()
                    .saturating_sub((c.margin[0] + c.margin[2]).max(0) as u32)
            },
            if horizontal {
                measure(s, *child, true, depth + 1)?
            } else {
                area.width()
            },
        );
        let height = dimension(
            c.height,
            if !horizontal && n.layout != 2 && c.height == -1 {
                shared.max(1)
            } else {
                area.height()
                    .saturating_sub((c.margin[1] + c.margin[3]).max(0) as u32)
            },
            measure(s, *child, false, depth + 1)?,
        );
        if width > 0 && height > 0 {
            arrange(
                s,
                *child,
                Rect::new(
                    area.x() - n.scroll[0] + c.margin[0] + if horizontal { offset } else { 0 },
                    area.y() - n.scroll[1] + c.margin[1] + if n.layout == 1 { offset } else { 0 },
                    width,
                    height,
                ),
                result,
                depth + 1,
            )?;
        }
        if n.layout != 2 {
            offset += if horizontal {
                width as i32 + c.margin[0] + c.margin[2] + 14
            } else {
                height as i32 + c.margin[1] + c.margin[3] + 14
            };
        }
    }
    Ok(())
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
    let mut canvas = window.into_canvas().build().map_err(|e| e.to_string())?;
    eprintln!("PADBRIDGE_RENDERER={:?}", canvas.info());
    let texture_creator = canvas.texture_creator();
    let mut image_cache = std::collections::HashMap::new();
    let font = ttf.load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25)?;
    let mut events = sdl.event_pump()?;
    let mut previous_flags = -1;
    let mut targets: Vec<(usize, Rect)> = vec![];
    'running: loop {
        env.call_static_method("org/padtv/bridge/Host", "pump", "()V", &[])
            .map_err(|e| e.to_string())?;
        if env
            .call_static_method("org/padtv/bridge/Host", "isFinished", "()Z", &[])
            .map_err(|e| e.to_string())?
            .z()
            .map_err(|e| e.to_string())?
        {
            break;
        }
        for event in events.poll_iter() {
            match event {
                Event::Window {
                    win_event: sdl2::event::WindowEvent::FocusGained,
                    ..
                } => {
                    env.call_static_method(
                        "org/padtv/bridge/Host",
                        "windowFocus",
                        "(Z)V",
                        &[JValue::Bool(1)],
                    )
                    .map_err(|e| e.to_string())?;
                }
                Event::Window {
                    win_event: sdl2::event::WindowEvent::FocusLost,
                    ..
                } => {
                    env.call_static_method(
                        "org/padtv/bridge/Host",
                        "windowFocus",
                        "(Z)V",
                        &[JValue::Bool(0)],
                    )
                    .map_err(|e| e.to_string())?;
                }
                Event::Quit { .. } => break 'running,
                Event::KeyDown {
                    keycode: Some(k), ..
                } => {
                    if let Some(code) = key(k) {
                        env.call_static_method(
                            "org/padtv/bridge/Host",
                            "handleKeyAction",
                            "(II)V",
                            &[JValue::Int(code), JValue::Int(0)],
                        )
                        .map_err(|e| e.to_string())?;
                    }
                }
                Event::KeyUp {
                    keycode: Some(k), ..
                } => {
                    if let Some(code) = key(k) {
                        env.call_static_method(
                            "org/padtv/bridge/Host",
                            "handleKeyAction",
                            "(II)V",
                            &[JValue::Int(code), JValue::Int(1)],
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
        if state.window_flags != previous_flags {
            canvas
                .window_mut()
                .set_fullscreen(if state.window_flags & 1024 != 0 {
                    sdl2::video::FullscreenType::Desktop
                } else {
                    sdl2::video::FullscreenType::Off
                })?;
            if state.window_flags & 128 != 0 {
                video.disable_screen_saver();
            } else {
                video.enable_screen_saver();
            }
            previous_flags = state.window_flags;
        }
        let mut items = vec![];
        let (width, height) = canvas.output_size()?;
        let margin = if state.window_flags & 1024 != 0 {
            0
        } else {
            40
        };
        arrange(
            &state,
            state.root,
            Rect::new(
                margin as i32,
                margin as i32,
                width.saturating_sub(margin * 2).max(1),
                height.saturating_sub(margin * 2).max(1),
            ),
            &mut items,
            0,
        )?;
        for (id, area) in &items {
            env.call_static_method(
                "org/padtv/bridge/Host",
                "layout",
                "(IIIII)V",
                &[
                    JValue::Int(*id as i32),
                    JValue::Int(area.x()),
                    JValue::Int(area.y()),
                    JValue::Int(area.width() as i32),
                    JValue::Int(area.height() as i32),
                ],
            )
            .map_err(|e| e.to_string())?;
        }
        env.call_static_method("org/padtv/bridge/Host", "endLayout", "()V", &[])
            .map_err(|e| e.to_string())?;
        let draw = env
            .call_static_method("org/padtv/bridge/Host", "drawFrame", "()Z", &[])
            .map_err(|e| e.to_string())?
            .z()
            .map_err(|e| e.to_string())?;
        if !draw {
            std::thread::sleep(std::time::Duration::from_millis(16));
            continue;
        }
        let state = scene().lock().unwrap().clone();
        targets.clear();
        canvas.set_draw_color(Color::RGB(13, 28, 29));
        canvas.clear();
        for (id, area) in items {
            let node = &state.nodes[id];
            if node.kind == 2 {
                canvas.set_draw_color(if id == state.focus {
                    Color::RGB(88, 57, 180)
                } else {
                    Color::RGB(32, 65, 65)
                });
                canvas.fill_rect(area)?;
                targets.push((id, area));
            }
            if !node.image.is_empty() {
                let stale = image_cache
                    .get(&id)
                    .map_or(true, |(version, _)| *version != node.image_version);
                if stale {
                    image_cache.insert(
                        id,
                        (
                            node.image_version,
                            texture_creator.load_texture_bytes(&node.image)?,
                        ),
                    );
                }
                let texture = &image_cache[&id].1;
                let q = texture.query();
                let scale = (area.height() as f64 / q.height as f64)
                    .min(area.width() as f64 / q.width as f64);
                canvas.copy(
                    texture,
                    None,
                    Rect::new(
                        area.x(),
                        area.y(),
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
                    Rect::new(
                        area.x() + 14,
                        area.y() + 14,
                        surface.width(),
                        surface.height(),
                    ),
                )?;
            }
        }
        canvas.present();
        std::thread::sleep(std::time::Duration::from_millis(16));
    }
    Ok(())
}
#[no_mangle]
pub extern "system" fn Java_org_padtv_bridge_Native_layoutScene(
    mut env: JNIEnv,
    _: JClass,
    width: jint,
    height: jint,
) {
    if width < 1 || height < 1 || width > 4096 || height > 4096 {
        fail(&mut env, "Invalid test surface size");
        return;
    }
    let state = scene().lock().unwrap().clone();
    let mut items = vec![];
    if let Err(e) = arrange(
        &state,
        state.root,
        Rect::new(0, 0, width as u32, height as u32),
        &mut items,
        0,
    ) {
        fail(&mut env, e);
        return;
    }
    for (id, rect) in items {
        if let Err(e) = env.call_static_method(
            "org/padtv/bridge/Host",
            "layout",
            "(IIIII)V",
            &[
                JValue::Int(id as i32),
                JValue::Int(rect.x()),
                JValue::Int(rect.y()),
                JValue::Int(rect.width() as i32),
                JValue::Int(rect.height() as i32),
            ],
        ) {
            fail(&mut env, e);
            return;
        }
    }
    if let Err(e) = env.call_static_method("org/padtv/bridge/Host", "endLayout", "()V", &[]) {
        fail(&mut env, e);
        return;
    }
    if let Err(e) = env.call_static_method("org/padtv/bridge/Host", "drawFrame", "()Z", &[]) {
        fail(&mut env, e);
    }
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
