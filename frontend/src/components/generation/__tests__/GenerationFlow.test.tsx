import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { screen, waitFor } from '@testing-library/dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GenerationContainer } from '../GenerationContainer';
import * as generationHook from '@/hooks/useGenerationJob';

// Mock the useGenerationJob hook
vi.mock('@/hooks/useGenerationJob');

describe('GenerationFlow: Text-to-Image 전체 플로우', () => {
  let queryClient: QueryClient;
  let mockStartJob: ReturnType<typeof vi.fn>;
  let mockReset: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockStartJob = vi.fn().mockResolvedValue(undefined);
    mockReset = vi.fn();

    // Default mock: idle state
    vi.mocked(generationHook.useGenerationJob).mockReturnValue({
      startJob: mockStartJob,
      jobStatus: 'idle',
      currentJob: null,
      error: null,
      reset: mockReset,
    });
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <GenerationContainer />
      </QueryClientProvider>
    );
  };

  describe('1️⃣ 정상 플로우: 프롬프트 입력 → 생성 → 결과 확인', () => {
    it('프롬프트를 입력하고 Generate 버튼을 누르면 생성 요청이 실행된다', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Arrange: 프롬프트 입력 (실제 placeholder 사용)
      const textarea = screen.getByPlaceholderText(/futuristic city/i);
      await user.type(textarea, 'A beautiful sunset over mountains');

      // Act: Generate 버튼 클릭
      const generateButton = screen.getByRole('button', { name: /^Generate$/i });
      await user.click(generateButton);

      // Assert: startJob이 올바른 인자로 호출되었는지
      expect(mockStartJob).toHaveBeenCalledWith(
        expect.objectContaining({
          prompt: 'A beautiful sunset over mountains',
          mode: 'text-to-image',
          model: 'imagen-3.0-fast-generate-001',
        })
      );
    });

    it('생성 중에는 "Generating" 로딩 UI가 표시된다', async () => {
      // Mock: processing 상태로 변경
      vi.mocked(generationHook.useGenerationJob).mockReturnValue({
        startJob: mockStartJob,
        jobStatus: 'processing',
        currentJob: null,
        error: null,
        reset: mockReset,
      });

      renderComponent();

      // Assert: 로딩 텍스트 확인 (헤딩으로 특정)
      expect(screen.getByRole('heading', { name: /generating/i })).toBeInTheDocument();
    });

    it('생성이 완료되면 결과 이미지가 화면에 표시된다', async () => {
      // Mock: completed 상태
      vi.mocked(generationHook.useGenerationJob).mockReturnValue({
        startJob: mockStartJob,
        jobStatus: 'completed',
        currentJob: {
          job_id: 'test-job-123',
          status: 'completed',
          result_url: 'https://example.com/result.jpg',
          created_at: new Date().toISOString(),
        },
        error: null,
        reset: mockReset,
      });

      renderComponent();

      // Assert: 결과 이미지 또는 완료 메시지 확인
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /generation complete/i })).toBeInTheDocument();
      });

      // 이미지 태그 확인
      const resultImage = screen.getByAltText(/generated content/i);
      expect(resultImage).toHaveAttribute('src', expect.stringContaining('result.jpg'));
    });
  });

  describe('2️⃣ 빈 프롬프트 검증', () => {
    it('빈 프롬프트로 생성 시도 시 Generate 버튼이 비활성화된다', async () => {
      renderComponent();

      // Assert: 빈 상태에서 버튼은 disabled
      const generateButton = screen.getByRole('button', { name: /^Generate$/i });
      expect(generateButton).toBeDisabled();
    });
  });

  describe('3️⃣ 재생성(Generate New)', () => {
    it('Generate New 버튼 클릭 시 마지막 설정으로 다시 생성 요청한다', async () => {
      const user = userEvent.setup();
      const { rerender } = renderComponent();

      // Step 1: 먼저 정상적으로 생성 요청 (lastConfig 설정됨)
      const textarea = screen.getByPlaceholderText(/futuristic city/i);
      await user.type(textarea, 'Test prompt for regeneration');
      const generateButton = screen.getByRole('button', { name: /^Generate$/i });
      await user.click(generateButton);

      // Step 2: 완료 상태로 Mock 변경
      vi.mocked(generationHook.useGenerationJob).mockReturnValue({
        startJob: mockStartJob,
        jobStatus: 'completed',
        currentJob: {
          job_id: 'test-job-123',
          status: 'completed',
          result_url: 'https://example.com/result.jpg',
          created_at: new Date().toISOString(),
        },
        error: null,
        reset: mockReset,
      });

      // Step 3: 리렌더링하여 완료 UI 표시
      rerender(
        <QueryClientProvider client={queryClient}>
          <GenerationContainer />
        </QueryClientProvider>
      );

      // Step 4: "Generate New" 버튼 클릭
      const regenerateButton = screen.getByRole('button', { name: /generate new/i });
      await user.click(regenerateButton);

      // Assert: startJob이 재호출됨 (처음 1번 + 재생성 1번 = 총 2번)
      expect(mockStartJob).toHaveBeenCalledTimes(2);
    });
  });

  describe('4️⃣ 에러 핸들링', () => {
    it('생성 실패 시 에러 메시지가 표시된다', async () => {
      // Mock: failed 상태
      vi.mocked(generationHook.useGenerationJob).mockReturnValue({
        startJob: mockStartJob,
        jobStatus: 'failed',
        currentJob: null,
        error: 'Generation failed due to server error',
        reset: mockReset,
      });

      renderComponent();

      // Assert: 에러 메시지 확인 (헤딩으로 특정)
      expect(screen.getByRole('heading', { name: /generation failed/i })).toBeInTheDocument();
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
      
      // Try Again 버튼이 렌더링되는지 확인
      expect(screen.getByRole('button', { name: /^Try Again$/i })).toBeInTheDocument();
    });
  });

  describe('5️⃣ 프롬프트 초기화 (Generate 후)', () => {
    it('Generate 버튼을 누르면 입력창이 비워진다', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Arrange: 프롬프트 입력
      const textarea = screen.getByPlaceholderText(/futuristic city/i) as HTMLTextAreaElement;
      await user.type(textarea, 'Mountain view');

      // Act: Generate 클릭
      const generateButton = screen.getByRole('button', { name: /^Generate$/i });
      await user.click(generateButton);

      // Assert: textarea가 비워짐
      await waitFor(() => {
        expect(textarea.value).toBe('');
      });
    });
  });
});
