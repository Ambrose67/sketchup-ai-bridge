require 'sketchup.rb'
require 'extensions.rb'

module RoseSketchupBridge
  unless file_loaded?(__FILE__)
    extension = SketchupExtension.new('SketchUp AI Bridge', 'rose_sketchup_bridge/main')
    extension.description = 'Local, explicit modeling commands for AI assistants.'
    extension.version = '0.1.0'
    extension.creator = 'SketchUp AI Bridge contributors'
    Sketchup.register_extension(extension, true)
    file_loaded(__FILE__)
  end
end
