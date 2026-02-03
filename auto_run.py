import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import time
import threading

from modules.caldera.executor import CalderaExecutor
from modules.caldera.uploader import CalderaUploader
from modules.caldera.agent_manager import AgentManager
from modules.core.config import get_caldera_url, get_caldera_api_key
from scripts import vm_reload


class CalderaPipelineRunner:
    def __init__(self, n_iterations=1, project_root=None):
        """
        Args:
            n_iterations: 전체 TTPs 세트를 반복할 횟수
            project_root: 프로젝트 루트 경로 (기본값: 현재 스크립트 위치)
        """
        self.n_iterations = n_iterations
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.auto_run_dir = self.project_root / "data" / "processed" / "auto-run"
        self.auto_run_dir.mkdir(exist_ok=True)

        # 실행 시간 추적용
        self.execution_times = []  # 각 TTPs 실행 시간 기록
        # 현재 실행 중인 TTPs 번호 (강제 종료 시 정리용)
        self.current_ttps_num = None

        # TTPs 설정 정보 (문서 기반)
        self.ttps_configs = {
            1: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps1',
                    'VBOX_SNAPSHOT_NAME': 'ttps1',
                    'VBOX_VM_NAME_lateral': 'ttps1_2',
                    'VBOX_SNAPSHOT_NAME_lateral': 'ttps1_2',
                },
                'env_comments': ['VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_1.pdf',
                'env': 'environment_ttps1.md'
            },
            2: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps2',
                    'VBOX_SNAPSHOT_NAME': 'ttps2',
                },
                'env_comments': ['VBOX_VM_NAME_lateral', 'VBOX_SNAPSHOT_NAME_lateral',
                               'VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_2.pdf',
                'env': 'environment_ttps2.md'
            },
            3: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps3',
                    'VBOX_SNAPSHOT_NAME': 'ttps3',
                },
                'env_comments': ['VBOX_VM_NAME_lateral', 'VBOX_SNAPSHOT_NAME_lateral',
                               'VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_3.pdf',
                'env': 'environment_ttps3.md'
            },
            4: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps4',
                    'VBOX_SNAPSHOT_NAME': 'ttps4',
                },
                'env_comments': ['VBOX_VM_NAME_lateral', 'VBOX_SNAPSHOT_NAME_lateral',
                               'VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_4.pdf',
                'env': 'environment_ttps4.md'
            },
            5: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps5',
                    'VBOX_SNAPSHOT_NAME': 'ttps5',
                    'VBOX_VM_NAME_lateral': 'ttps5_2',
                    'VBOX_SNAPSHOT_NAME_lateral': 'ttps5_2',
                    'VBOX_VM_NAME_ad': 'ttps5_ad',
                    'VBOX_SNAPSHOT_NAME_ad': 'ttps5_ad',
                },
                'env_comments': [],
                'pdf': 'data/raw/KISA_TTPs_5.pdf',
                'env': 'environment_ttps5.md'
            },
            6: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps6',
                    'VBOX_SNAPSHOT_NAME': 'ttps6',
                },
                'env_comments': ['VBOX_VM_NAME_lateral', 'VBOX_SNAPSHOT_NAME_lateral',
                               'VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_6.pdf',
                'env': 'environment_ttps6.md'
            },
            7: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps7',
                    'VBOX_SNAPSHOT_NAME': 'ttps7',
                    'VBOX_VM_NAME_lateral': 'ttps7_2',
                    'VBOX_SNAPSHOT_NAME_lateral': 'ttps7_2',
                },
                'env_comments': ['VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_7.pdf',
                'env': 'environment_ttps7.md'
            },
            8: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps8',
                    'VBOX_SNAPSHOT_NAME': 'ttps8',
                    'VBOX_VM_NAME_lateral': 'ttps8_2',
                    'VBOX_SNAPSHOT_NAME_lateral': 'ttps8_2',
                    'VBOX_VM_NAME_ad': 'ttps8_ad',
                    'VBOX_SNAPSHOT_NAME_ad': 'ttps8_ad',
                },
                'env_comments': [],
                'pdf': 'data/raw/KISA_TTPs_8.pdf',
                'env': 'environment_ttps8.md'
            },
            9: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps9',
                    'VBOX_SNAPSHOT_NAME': 'ttps9',
                },
                'env_comments': ['VBOX_VM_NAME_lateral', 'VBOX_SNAPSHOT_NAME_lateral',
                               'VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_9.pdf',
                'env': 'environment_ttps9.md'
            },
            10: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps10',
                    'VBOX_SNAPSHOT_NAME': 'ttps10',
                    'VBOX_VM_NAME_lateral': 'ttps10_2',
                    'VBOX_SNAPSHOT_NAME_lateral': 'ttps10_2',
                },
                'env_comments': ['VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_10.pdf',
                'env': 'environment_ttps10.md'
            },
            11: {
                'env_updates': {
                    'VBOX_VM_NAME': 'ttps11',
                    'VBOX_SNAPSHOT_NAME': 'ttps11',
                    'VBOX_VM_NAME_lateral': 'ttps11_2',
                    'VBOX_SNAPSHOT_NAME_lateral': 'ttps11_2',
                },
                'env_comments': ['VBOX_VM_NAME_ad', 'VBOX_SNAPSHOT_NAME_ad'],
                'pdf': 'data/raw/KISA_TTPs_11.pdf',
                'env': 'environment_ttps11.md'
            },
        }

    def update_env_file(self, env_updates, env_comments):
        """
        .env 파일 업데이트 (기존 주석, 빈 줄, 순서 보존)
        env_updates: 설정할 환경변수 dict
        env_comments: 주석 처리할 환경변수 키 list
        """
        env_path = self.project_root / '.env'

        # 기존 .env 파일을 라인 단위로 읽기
        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        # 처리할 VBOX_ 키 목록 (업데이트 대상 + 주석 처리 대상)
        all_vbox_keys = set(env_updates.keys()) | set(env_comments)

        # 기존 라인을 순회하며 VBOX_ 관련 라인만 교체/주석 처리
        new_lines = []
        written_keys = set()

        for line in lines:
            line_stripped = line.strip()

            # 주석 처리된 VBOX_ 라인 (# VBOX_VM_NAME= 형태)
            if line_stripped.startswith('#'):
                # "# KEY=" 또는 "# KEY=value" 패턴 확인
                uncommented = line_stripped.lstrip('#').strip()
                if '=' in uncommented:
                    key = uncommented.split('=', 1)[0].strip()
                    if key in all_vbox_keys:
                        # 업데이트 대상이면 활성화, 주석 대상이면 주석 유지
                        if key in env_updates and key not in written_keys:
                            new_lines.append(f"{key}={env_updates[key]}\n")
                            written_keys.add(key)
                        elif key in env_comments and key not in written_keys:
                            new_lines.append(f"# {key}=\n")
                            written_keys.add(key)
                        continue
                # VBOX_와 무관한 주석은 그대로 유지
                new_lines.append(line)
            # 활성 환경변수 라인
            elif '=' in line_stripped and line_stripped:
                key = line_stripped.split('=', 1)[0].strip()
                if key in env_updates and key not in written_keys:
                    new_lines.append(f"{key}={env_updates[key]}\n")
                    written_keys.add(key)
                elif key in env_comments and key not in written_keys:
                    new_lines.append(f"# {key}=\n")
                    written_keys.add(key)
                elif key not in all_vbox_keys:
                    new_lines.append(line)
            else:
                # 빈 줄 등 그대로 유지
                new_lines.append(line)

        # 기존 .env에 없던 새 VBOX_ 키가 있으면 끝에 추가
        for key, value in env_updates.items():
            if key not in written_keys:
                new_lines.append(f"{key}={value}\n")
        for key in env_comments:
            if key not in written_keys:
                new_lines.append(f"# {key}=\n")

        # .env 파일 쓰기
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    def format_timedelta(self, td):
        """
        timedelta를 읽기 쉬운 형식으로 변환
        """
        if td is None:
            return "계산 중..."

        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초"

    def _kill_process_tree(self, process):
        """프로세스와 모든 자식 프로세스 강제 종료 (Windows)"""
        try:
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                capture_output=True
            )
        except Exception:
            process.kill()

    def cleanup_after_timeout(self):
        """타임아웃 또는 강제 종료 후 잔여 환경 정리

        1. 실행 중인 모든 Caldera Operation 중단
        2. 업로드된 Ability/Adversary 삭제
        3. Caldera 에이전트 정리
        4. VM 종료
        """
        print("\n[정리] 강제 종료 후 환경 정리 시작...")

        # 1. 실행 중인 Operation 중단
        try:
            executor = CalderaExecutor(get_caldera_url(), get_caldera_api_key())
            stopped = executor.stop_all_running_operations()
            print(f"  [OK] 실행 중인 Operation {stopped}개 중단")
        except Exception as e:
            print(f"  [WARNING] Operation 중단 실패: {e}")

        # 2. 업로드된 Ability/Adversary 삭제
        if self.current_ttps_num is not None:
            try:
                config = self.ttps_configs[self.current_ttps_num]
                pdf_stem = Path(config['pdf']).stem
                # 가장 최근 버전 디렉토리에서 abilities.yml / adversaries.yml 찾기
                ttps_dir = self.project_root / "data" / "processed" / pdf_stem
                if ttps_dir.exists():
                    version_dirs = sorted(ttps_dir.iterdir(), reverse=True)
                    for version_dir in version_dirs:
                        caldera_dir = version_dir / "caldera"
                        abilities_file = caldera_dir / "abilities.yml"
                        adversaries_file = caldera_dir / "adversaries.yml"
                        if abilities_file.exists() or adversaries_file.exists():
                            import yaml
                            uploader = CalderaUploader()
                            if abilities_file.exists():
                                with open(abilities_file, 'r', encoding='utf-8') as f:
                                    abilities = yaml.safe_load(f) or []
                                ids = [a.get('ability_id') for a in abilities if a.get('ability_id')]
                                if ids:
                                    deleted = uploader.delete_abilities(ids)
                                    print(f"  [OK] Ability {deleted}/{len(ids)}개 삭제")
                            if adversaries_file.exists():
                                with open(adversaries_file, 'r', encoding='utf-8') as f:
                                    adversaries = yaml.safe_load(f) or []
                                ids = [a.get('adversary_id') for a in adversaries if a.get('adversary_id')]
                                if ids:
                                    deleted = uploader.delete_adversaries(ids)
                                    print(f"  [OK] Adversary {deleted}/{len(ids)}개 삭제")
                            break
            except Exception as e:
                print(f"  [WARNING] Ability/Adversary 삭제 실패: {e}")

        # 3. Caldera 에이전트 정리
        try:
            agent_manager = AgentManager()
            agent_manager.kill_all_agents()
            print("  [OK] Caldera 에이전트 정리 완료")
        except Exception as e:
            print(f"  [WARNING] 에이전트 정리 실패: {e}")

        # 4. 현재 TTPs의 VM 종료 (config에서 직접 VM 이름을 가져와 확실하게 종료)
        try:
            controller = vm_reload.VBoxController()
            if self.current_ttps_num is not None:
                config = self.ttps_configs[self.current_ttps_num]
                vm_names = []
                for key in ('VBOX_VM_NAME', 'VBOX_VM_NAME_lateral', 'VBOX_VM_NAME_ad'):
                    name = config['env_updates'].get(key)
                    if name:
                        vm_names.append(name)
                for vm_name in vm_names:
                    try:
                        state = controller.get_state(vm_name)
                        if state == "running":
                            controller.stop_vm(vm_name, force=True)
                            print(f"  [OK] VM {vm_name} 종료 완료")
                    except Exception as e:
                        print(f"  [WARNING] VM {vm_name} 종료 실패: {e}")
            else:
                controller.shutdown_all()
                print("  [OK] VM 종료 완료")
        except Exception as e:
            print(f"  [WARNING] VM 종료 실패: {e}")

        print("[정리] 환경 정리 완료\n")

    def run_pipeline(self, ttps_num, iteration, total_iterations, timeout=3600):
        """
        특정 TTPs에 대한 파이프라인 실행

        Args:
            timeout: 최대 실행 시간 (초, 기본값: 3600 = 1시간)

        Returns:
            str: "success", "failed", "timeout"
        """
        self.current_ttps_num = ttps_num
        config = self.ttps_configs[ttps_num]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 로그 디렉토리 생성
        log_dir = self.auto_run_dir / f"KISA_TTPs_{ttps_num}" / timestamp
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "execution.log"

        # .env 파일 업데이트
        self.update_env_file(config['env_updates'], config['env_comments'])

        # 자식 프로세스용 환경변수 구성
        # subprocess는 부모의 os.environ을 상속하고, load_dotenv()는 이미 존재하는
        # 환경변수를 덮어쓰지 않으므로, .env 파일 변경이 무시될 수 있음.
        # 따라서 VBOX_ 관련 변수를 명시적으로 설정하고, 주석 처리 대상은 제거함.
        child_env = os.environ.copy()
        for key, value in config['env_updates'].items():
            child_env[key] = value
        for key in config['env_comments']:
            child_env.pop(key, None)

        # main.py 실행 명령어 구성
        cmd = [
            'python', 'main.py',
            '--step', 'all',
            '--pdf', config['pdf'],
            '--env', config['env']
        ]

        # 실행 시작 시간
        start_time = time.time()

        # 타임아웃 감지용 플래그
        timed_out = False

        def timeout_handler():
            nonlocal timed_out
            timed_out = True
            print(f"\n⏰ TTPs {ttps_num} 타임아웃 ({timeout//60}분 초과) - 프로세스 강제 종료")
            self._kill_process_tree(process)

        # 명령어 실행 및 로그 저장
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                # 실행 정보 기록
                f.write(f"실행 시간: {timestamp}\n")
                f.write(f"TTPs: {ttps_num}\n")
                f.write(f"반복: {iteration}/{total_iterations}\n")
                f.write(f"타임아웃: {timeout//60}분\n")
                f.write(f"명령어: {' '.join(cmd)}\n")
                f.write(f"환경 설정:\n")
                for key, value in config['env_updates'].items():
                    f.write(f"  {key}={value}\n")
                if config['env_comments']:
                    f.write(f"주석 처리된 설정: {', '.join(config['env_comments'])}\n")
                f.write(f"{'='*80}\n\n")
                f.flush()

                # 프로세스 실행 (child_env로 VBOX_ 환경변수를 명시적으로 전달)
                process = subprocess.Popen(
                    cmd,
                    cwd=self.project_root,
                    env=child_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    bufsize=1
                )

                # 타임아웃 타이머 시작
                timer = threading.Timer(timeout, timeout_handler)
                timer.start()

                try:
                    # 실시간 로그 출력 및 저장
                    for line in process.stdout:
                        print(line, end='')
                        f.write(line)
                        f.flush()

                    # 프로세스 종료 대기
                    return_code = process.wait()
                finally:
                    timer.cancel()

                # 실행 시간 기록
                execution_time = time.time() - start_time
                self.execution_times.append(execution_time)

                # 종료 상태 기록
                f.write(f"\n{'='*80}\n")
                f.write(f"실행 시간: {self.format_timedelta(timedelta(seconds=int(execution_time)))}\n")

                if timed_out:
                    f.write(f"종료 사유: 타임아웃 ({timeout//60}분 초과)\n")
                    return "timeout"
                elif return_code == 0:
                    f.write(f"종료 코드: {return_code}\n")
                    print(f"✓ TTPs {ttps_num} 실행 완료 (성공) - 소요 시간: {self.format_timedelta(timedelta(seconds=int(execution_time)))}")
                    return "success"
                else:
                    f.write(f"종료 코드: {return_code}\n")
                    print(f"✗ TTPs {ttps_num} 실행 완료 (오류 발생: 코드 {return_code})")
                    return "failed"

        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_times.append(execution_time)
            error_msg = f"오류 발생: {str(e)}"
            print(f"✗ {error_msg}")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{error_msg}\n")
                f.write(f"실행 시간: {self.format_timedelta(timedelta(seconds=int(execution_time)))}\n")
            return "failed"

    def run_all(self, max_retries=3, timeout=3600):
        """
        전체 실험 실행 (TTPs 1-11을 n번 반복)

        Args:
            max_retries: 타임아웃 시 최대 재시도 횟수
            timeout: TTPs 하나당 최대 실행 시간 (초)
        """
        total_runs = 11 * self.n_iterations
        results = []

        print(f"\n{'#'*80}")
        print(f"Caldera Pipeline 자동 실행 시작")
        print(f"총 반복 횟수: {self.n_iterations}")
        print(f"총 실행 횟수: {total_runs} (TTPs 1-11 × {self.n_iterations})")
        print(f"타임아웃: {timeout//60}분 | 최대 재시도: {max_retries}회")
        print(f"프로젝트 경로: {self.project_root}")
        print(f"로그 저장 경로: {self.auto_run_dir}")
        print(f"{'#'*80}\n")

        start_time = datetime.now()

        # n번 반복
        for iteration in range(1, self.n_iterations + 1):
            print(f"\n{'='*80}")
            print(f"반복 {iteration}/{self.n_iterations} 시작")
            print(f"{'='*80}\n")

            # TTPs 1-11 순차 실행
            for ttps_num in range(1, 12):
                current_run = (iteration - 1) * 11 + ttps_num

                # 재시도 루프
                for attempt in range(1, max_retries + 1):
                    if attempt == 1:
                        print(f"\n[{current_run}/{total_runs}] TTPs {ttps_num} 실행 시작...")
                    else:
                        print(f"\n[{current_run}/{total_runs}] TTPs {ttps_num} 재시도 ({attempt}/{max_retries})...")

                    result = self.run_pipeline(ttps_num, iteration, self.n_iterations, timeout=timeout)

                    if result == "timeout" and attempt < max_retries:
                        print(f"  ↻ 타임아웃으로 재시도합니다...")
                        self.cleanup_after_timeout()
                        continue

                    # 성공이거나, 일반 실패이거나, 마지막 재시도면 결과 기록
                    if result == "timeout":
                        self.cleanup_after_timeout()
                    break

                results.append({
                    'iteration': iteration,
                    'ttps': ttps_num,
                    'result': result,
                    'attempts': attempt,
                    'run_number': current_run
                })

                # 현재까지의 성공률 출력
                completed = len(results)
                success_count = sum(1 for r in results if r['result'] == 'success')
                success_rate = success_count / completed * 100
                status_icon = '✓' if result == 'success' else '⏰' if result == 'timeout' else '✗'
                retry_info = f" ({attempt}회 시도)" if attempt > 1 else ""
                print(f"  {status_icon} 진행: {completed}/{total_runs} | 성공률: {success_rate:.1f}%{retry_info}")

        # 최종 결과 출력
        end_time = datetime.now()
        duration = end_time - start_time

        success_count = sum(1 for r in results if r['result'] == 'success')
        failed_count = sum(1 for r in results if r['result'] == 'failed')
        timeout_count = sum(1 for r in results if r['result'] == 'timeout')

        print(f"\n{'#'*80}")
        print(f"전체 실험 완료")
        print(f"{'#'*80}\n")
        print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"총 소요 시간: {self.format_timedelta(duration)}")
        print(f"\n실행 결과:")
        print(f"- 성공: {success_count}/{total_runs} ({success_count/total_runs*100:.1f}%)")
        print(f"- 실패: {failed_count}/{total_runs} ({failed_count/total_runs*100:.1f}%)")
        print(f"- 타임아웃: {timeout_count}/{total_runs} ({timeout_count/total_runs*100:.1f}%)")

        if self.execution_times:
            avg_time = sum(self.execution_times) / len(self.execution_times)
            min_time = min(self.execution_times)
            max_time = max(self.execution_times)
            print(f"\n실행 시간 통계:")
            print(f"- 평균: {self.format_timedelta(timedelta(seconds=int(avg_time)))}")
            print(f"- 최소: {self.format_timedelta(timedelta(seconds=int(min_time)))}")
            print(f"- 최대: {self.format_timedelta(timedelta(seconds=int(max_time)))}")

        # 실패/타임아웃 항목 출력
        not_success = [r for r in results if r['result'] != 'success']
        if not_success:
            print(f"\n실패/타임아웃 목록:")
            for r in not_success:
                status = "타임아웃" if r['result'] == 'timeout' else "실패"
                retry_info = f" ({r['attempts']}회 시도)" if r['attempts'] > 1 else ""
                print(f"  - 반복 {r['iteration']}, TTPs {r['ttps']}: {status}{retry_info}")

        # 전체 결과를 파일로 저장
        summary_file = self.auto_run_dir / f"summary_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Caldera Pipeline 자동 실행 결과\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"총 소요 시간: {self.format_timedelta(duration)}\n")
            f.write(f"반복 횟수: {self.n_iterations}\n")
            f.write(f"총 실행 횟수: {total_runs}\n")
            f.write(f"타임아웃: {timeout//60}분 | 최대 재시도: {max_retries}회\n\n")
            f.write(f"성공: {success_count}/{total_runs} ({success_count/total_runs*100:.1f}%)\n")
            f.write(f"실패: {failed_count}/{total_runs} ({failed_count/total_runs*100:.1f}%)\n")
            f.write(f"타임아웃: {timeout_count}/{total_runs} ({timeout_count/total_runs*100:.1f}%)\n\n")

            if self.execution_times:
                avg_time = sum(self.execution_times) / len(self.execution_times)
                min_time = min(self.execution_times)
                max_time = max(self.execution_times)
                f.write(f"실행 시간 통계:\n")
                f.write(f"- 평균: {self.format_timedelta(timedelta(seconds=int(avg_time)))}\n")
                f.write(f"- 최소: {self.format_timedelta(timedelta(seconds=int(min_time)))}\n")
                f.write(f"- 최대: {self.format_timedelta(timedelta(seconds=int(max_time)))}\n\n")

            if not_success:
                f.write(f"실패/타임아웃 목록:\n")
                for r in not_success:
                    status = "타임아웃" if r['result'] == 'timeout' else "실패"
                    retry_info = f" ({r['attempts']}회 시도)" if r['attempts'] > 1 else ""
                    f.write(f"  - 반복 {r['iteration']}, TTPs {r['ttps']}: {status}{retry_info}\n")

            f.write(f"\n{'='*80}\n")
            f.write(f"상세 결과:\n\n")
            for r in results:
                status_map = {'success': '성공', 'failed': '실패', 'timeout': '타임아웃'}
                status = status_map.get(r['result'], r['result'])
                retry_info = f" ({r['attempts']}회 시도)" if r['attempts'] > 1 else ""
                f.write(f"[{r['run_number']:2d}/{total_runs}] 반복 {r['iteration']}, TTPs {r['ttps']:2d}: {status}{retry_info}\n")

        print(f"\n전체 결과가 저장되었습니다: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Caldera Pipeline 자동 실행 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
사용 예시:
  python auto_run.py -n 2              # TTPs 1-11을 2번 반복
  python auto_run.py -n 5 -p /path    # 특정 경로에서 5번 반복
        '''
    )

    parser.add_argument(
        '-n', '--iterations',
        type=int,
        default=1,
        help='전체 TTPs 세트를 반복할 횟수 (기본값: 1)'
    )

    parser.add_argument(
        '-p', '--project-root',
        type=str,
        default=None,
        help='프로젝트 루트 경로 (기본값: 현재 디렉토리)'
    )

    args = parser.parse_args()

    # 반복 횟수 검증
    if args.iterations < 1:
        print("오류: 반복 횟수는 1 이상이어야 합니다.")
        sys.exit(1)

    # 실행
    runner = CalderaPipelineRunner(
        n_iterations=args.iterations,
        project_root=args.project_root
    )

    try:
        runner.run_all()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        runner.cleanup_after_timeout()
        sys.exit(1)
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        runner.cleanup_after_timeout()
        sys.exit(1)


if __name__ == '__main__':
    main()
