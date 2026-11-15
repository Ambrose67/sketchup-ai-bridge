require 'sketchup.rb'
require 'json'
require 'fileutils'

module RoseSketchupBridge
  DIR = File.join(Dir.home, '.sketchup-ai-bridge')
  REQUESTS = File.join(DIR, 'requests')
  RESPONSES = File.join(DIR, 'responses')

  def self.number(value, label, positive = false)
    raise ArgumentError, "#{label} must be a number" unless value.is_a?(Numeric) && value.finite?
    raise ArgumentError, "#{label} must be positive" if positive && value <= 0
    raise ArgumentError, "#{label} is too large" if value.abs > 1_000_000
    value.to_f / 25.4 # millimetres to SketchUp internal inches
  end

  def self.execute(request)
    model = Sketchup.active_model
    args = request.fetch('arguments', {})
    case request.fetch('command')
    when 'model_info'
      { 'title' => model.title, 'path' => model.path, 'units' => 'mm',
        'root_entity_count' => model.entities.length,
        'selection_count' => model.selection.length }
    when 'list_groups'
      { 'groups' => model.entities.grep(Sketchup::Group).first(500).map { |g|
        { 'id' => g.persistent_id, 'name' => g.name,
          'bounds_mm' => [g.bounds.width, g.bounds.depth, g.bounds.height].map { |v| (v.to_f * 25.4).round(2) } }
      }, 'note' => 'Top-level groups only, limited to 500.' }
    when 'create_box'
      x = number(args.fetch('x_mm', 0), 'x_mm')
      y = number(args.fetch('y_mm', 0), 'y_mm')
      z = number(args.fetch('z_mm', 0), 'z_mm')
      w = number(args.fetch('width_mm'), 'width_mm', true)
      d = number(args.fetch('depth_mm'), 'depth_mm', true)
      h = number(args.fetch('height_mm'), 'height_mm', true)
      name = args.fetch('name', 'AI box')
      raise ArgumentError, 'name must be text up to 100 characters' unless name.is_a?(String) && name.length <= 100
      model.start_operation('AI Bridge: Create box', true)
      begin
        group = model.entities.add_group
        group.name = name
        face = group.entities.add_face([x,y,z], [x+w,y,z], [x+w,y+d,z], [x,y+d,z])
        raise 'Could not create face; check dimensions' unless face
        face.reverse! if face.normal.z < 0
        face.pushpull(h)
        model.commit_operation
        { 'id' => group.persistent_id, 'name' => group.name, 'units' => 'mm' }
      rescue StandardError
        model.abort_operation
        raise
      end
    else
      raise ArgumentError, 'Unknown command'
    end
  end

  def self.poll
    Dir.glob(File.join(REQUESTS, '*.json')).sort.first(10).each do |path|
      id = File.basename(path, '.json')
      next unless id.match?(/\A[0-9a-f]{32}\z/)
      begin
        request = JSON.parse(File.read(path))
        File.delete(path) # claim once; never replay after a crash
        raise 'Request expired before SketchUp processed it' if Time.now.to_f > request.fetch('expires_at').to_f
        result = { 'ok' => true, 'result' => execute(request) }
      rescue StandardError => e
        File.delete(path) if File.exist?(path)
        result = { 'ok' => false, 'error' => "#{e.class}: #{e.message}" }
      end
      tmp = File.join(RESPONSES, "#{id}.tmp")
      File.write(tmp, JSON.generate(result))
      File.rename(tmp, File.join(RESPONSES, "#{id}.json"))
    end
  rescue StandardError => e
    warn "SketchUp AI Bridge: #{e.message}"
  end

  unless file_loaded?(__FILE__)
    [DIR, REQUESTS, RESPONSES].each { |p| FileUtils.mkdir_p(p, mode: 0700) }
    UI.start_timer(0.5, true) { poll }
    UI.menu('Extensions').add_item('SketchUp AI Bridge: Status') do
      UI.messagebox("SketchUp AI Bridge is running.\nBridge folder: #{DIR}")
    end
    file_loaded(__FILE__)
  end
end
