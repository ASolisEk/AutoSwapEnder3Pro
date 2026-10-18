from autoswap.gcode import analyze, format_duration, is_tail_command_removable, job_commands


def test_analysis_tracks_relative_z_and_y(sample_gcode):
    info = analyze(sample_gcode)
    assert info.max_z == 15.2  # 5.2 + ascenso relativo de 10 mm del G-code final
    assert info.max_y == 235
    assert info.print_max_y == 150  # la linea de purga es lo mas lejano con extrusion
    assert info.est_seconds == 600
    assert info.has_home
    assert not info.errors


def test_tail_commands_that_break_the_swap_are_removed(sample_gcode):
    info = analyze(sample_gcode)
    removed = [r.split("  (")[0] for r in info.removed_tail]
    assert removed == ["G1 X0 Y235 F3000", "M140 S0", "M84"]
    sent = list(job_commands(info))
    assert "M84" not in sent
    assert "M140 S0" not in sent
    assert "G1 X0 Y235 F3000" not in sent
    assert "M140 S60" in sent  # el G-code inicial no se toca
    assert "G1 Z10 F600" in sent  # el ascenso final se conserva
    assert len(list(job_commands(info, strip_tail=False))) == info.lines


def test_too_tall_job_is_an_error(sample_gcode):
    info = analyze(sample_gcode, max_part_height=10)
    assert info.errors


def test_removable_rules():
    assert is_tail_command_removable("M18")
    assert is_tail_command_removable("M190 S0")
    assert not is_tail_command_removable("M104 S0")
    assert not is_tail_command_removable("G1 Z10")


def test_prusaslicer_time_and_duration_format(tmp_path):
    path = tmp_path / "p.gcode"
    path.write_text("; estimated printing time (normal mode) = 1h 2m 3s\nG28\nG1 X1 Y1 E1\n", encoding="utf-8")
    info = analyze(path)
    assert info.est_seconds == 3723
    assert format_duration(info.est_seconds) == "1 h 02 min"
    assert format_duration(None) == "?"
