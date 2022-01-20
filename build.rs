
extern crate protoc_rust;

use protoc_rust::Customize;

use std::env;
use std::fs;
use std::fs::File;
use std::io::Write;
use std::path::Path;

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join("protos");
    let proto_path = Path::new("./protos");
    fs::create_dir_all(&dest_path).unwrap();

    // Run protoc
    protoc_rust::Codegen::new()
        .out_dir(&dest_path.to_str().unwrap())
        .inputs(&[proto_path.join("pbft_message.proto").to_str().unwrap()])
        .includes(&[proto_path.to_str().unwrap()])
        .customize(Customize {
            serde_derive: Some(true),
            ..Default::default()
        })
        .run()
        .expect("Protoc Error");

    // Create mod.rs accordingly
    let mut mod_file = File::create(dest_path.join("mod.rs")).unwrap();
    mod_file.write_all(b"pub mod pbft_message;\n").unwrap();
}
