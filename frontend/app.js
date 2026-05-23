import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  updateProfile,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInAnonymously,
  sendPasswordResetEmail,
  sendEmailVerification,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyAltwdGZdj6RWKKKvc1cRIXTRA8IIs-5ZE",
  authDomain: "aistoryadventure-8796e.firebaseapp.com",
  projectId: "aistoryadventure-8796e",
  storageBucket: "aistoryadventure-8796e.firebasestorage.app",
  messagingSenderId: "587433707758",
  appId: "1:587433707758:web:2a1a36b90b9948fe7c8bff",
  measurementId: "G-EJW5P4ELFT",
};

const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);
window.auth = auth;
const provider = new GoogleAuthProvider();

const runtimeConfig = globalThis.AI_STORY_CONFIG || {};
const API_BASE = (runtimeConfig.API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
const ACCOUNT_STATUS_TIMEOUT_MS = 10000;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const loginPage      = document.getElementById("loginPage");
const landingPage    = document.getElementById("landingPage");
const setupPage      = document.getElementById("setupPage");
const gamePage       = document.getElementById("gamePage");
const foundationPage = document.getElementById("foundationPage");
const continuePage   = document.getElementById("continuePage");
const registerPage = document.getElementById("registerPage");
const forgotPasswordPage = document.getElementById("forgotPasswordPage");
const verifyEmailPage = document.getElementById("verifyEmailPage");
const novelWorldPage = document.getElementById("novelWorldPage");
const novelQuestionPage = document.getElementById("novelQuestionPage");
const novelCharacterPage = document.getElementById("novelCharacterPage");
const profilePage = document.getElementById("profilePage");
const trustPage = document.getElementById("trustPage");
const loginGoogleBtn          = document.getElementById("loginGoogleBtn");
const guestBtn                = document.getElementById("guestBtn");
const logoutBtn               = document.getElementById("logoutBtn");
const goToSetupBtn            = document.getElementById("goToSetup");
const startNovelBtn           = document.getElementById("startNovelBtn");
const continueBtn             = document.getElementById("continueBtn");
const backToLandingBtn        = document.getElementById("backToLanding");
const backToLandingFromContinue = document.getElementById("backToLandingFromContinue");
const rollBtn                 = document.getElementById("rollBtn");
const newGameBtn              = document.getElementById("newGameBtn");

const sessionLabel            = document.getElementById("sessionLabel");
const loadingOverlay          = document.getElementById("loadingOverlay");
const loadingEyebrow          = document.getElementById("loadingEyebrow");
const loadingTitle            = document.getElementById("loadingTitle");
const loadingRetryText        = document.getElementById("loadingRetryText");
const loadingElapsedText      = document.getElementById("loadingElapsedText");
const loadingHint             = document.getElementById("loadingHint");
const cancelLoadingBtn        = document.getElementById("cancelLoadingBtn");
const retryNowLoadingBtn      = document.getElementById("retryNowLoadingBtn");
const storyLog = document.getElementById("storyLog");
const choicesBox = document.getElementById("choicesBox");
const customAction = document.getElementById("customAction");
const submitBtn = document.getElementById("submitBtn");
const readerFocusToggle = document.getElementById("readerFocusToggle");
const readerFontDown = document.getElementById("readerFontDown");
const readerFontUp = document.getElementById("readerFontUp");
const readerLineDown = document.getElementById("readerLineDown");
const readerLineUp = document.getElementById("readerLineUp");
const scrollLatestBtn = document.getElementById("scrollLatestBtn");
const composerStatus = document.getElementById("composerStatus");
const foundationText          = document.getElementById("foundationText");
const backToSetupBtn = document.getElementById("backToSetupBtn");
const beginStoryBtn           = document.getElementById("beginStoryBtn");
const saveStoryFromFoundation = document.getElementById("saveStoryFromFoundation");
const foundationSaveStatus = document.getElementById("foundationSaveStatus");
const sessionList             = document.getElementById("sessionList");
const playerNameInput = document.getElementById("playerName");
const genderInput = document.getElementById("gender");
const personalityInput = document.getElementById("personality");
const storyStyleInput = document.getElementById("storyStyle");
const adventureOriginInput = document.getElementById("adventureOrigin");
const adventureGoalInput = document.getElementById("adventureGoal");
const adventureRiskInput = document.getElementById("adventureRisk");
const novelWorldSeed              = document.getElementById("novelWorldSeed");
const novelInitialTargetWords     = document.getElementById("novelInitialTargetWords");
const createNovelWorldBtn         = document.getElementById("createNovelWorldBtn");
const skipNovelWorldBtn           = document.getElementById("skipNovelWorldBtn");
const backToLandingFromNovelWorld = document.getElementById("backToLandingFromNovelWorld");

const novelQuestionTitle          = document.getElementById("novelQuestionTitle");
const novelQuestionStepLabel = document.getElementById("novelQuestionStepLabel");
const novelQuestionText           = document.getElementById("novelQuestionText");
const novelQuestionAnswer         = document.getElementById("novelQuestionAnswer");
const novelQuestionSuggestions    = document.getElementById("novelQuestionSuggestions");
const novelQuestionBackBtn        = document.getElementById("novelQuestionBackBtn");
const novelQuestionNextBtn        = document.getElementById("novelQuestionNextBtn");

const viewWorldDraftBtn           = document.getElementById("viewWorldDraftBtn");
const worldDraftModal             = document.getElementById("worldDraftModal");
const closeWorldDraftBtn          = document.getElementById("closeWorldDraftBtn");
const worldDraftText              = document.getElementById("worldDraftText");

const backToNovelQuestionsBtn     = document.getElementById("backToNovelQuestionsBtn");
const novelPlayerName             = document.getElementById("novelPlayerName");
const novelGender                 = document.getElementById("novelGender");
const novelAge                    = document.getElementById("novelAge");
const novelOccupation             = document.getElementById("novelOccupation");
const novelPersonality            = document.getElementById("novelPersonality");
const novelFoundationTargetWords  = document.getElementById("novelFoundationTargetWords");
const createNovelFoundationBtn    = document.getElementById("createNovelFoundationBtn");
const novelNameError              = document.getElementById("novelNameError");
const novelTargetWordsError       = document.getElementById("novelTargetWordsError");
const novelCharacterFormError     = document.getElementById("novelCharacterFormError");
const novelPreviewName            = document.getElementById("novelPreviewName");
const novelPreviewIdentity        = document.getElementById("novelPreviewIdentity");
const novelPreviewRole            = document.getElementById("novelPreviewRole");
const novelPreviewTargetWords     = document.getElementById("novelPreviewTargetWords");
const novelPreviewAnswers         = document.getElementById("novelPreviewAnswers");
const novelPreviewPersonality     = document.getElementById("novelPreviewPersonality");
const novelPreviewWorld           = document.getElementById("novelPreviewWorld");
const novelCharacterChips         = document.querySelectorAll(".novel-character-chip");

const turnTargetWords             = document.getElementById("turnTargetWords");

const userBadge      = document.getElementById("userBadge");
const userAvatarImg  = document.getElementById("userAvatarImg");
const userNameLabel  = document.getElementById("userNameLabel");
const userEmailLabel = document.getElementById("userEmailLabel");

const profileAvatar = document.getElementById("profileAvatar");
const profileDisplayName = document.getElementById("profileDisplayName");
const profileEmail = document.getElementById("profileEmail");
const profileLoginState = document.getElementById("profileLoginState");
const profileEditNameBtn = document.getElementById("profileEditNameBtn");
const profileNameEditPanel = document.getElementById("profileNameEditPanel");
const profileNameInput = document.getElementById("profileNameInput");
const profileNameSaveBtn = document.getElementById("profileNameSaveBtn");
const profileNameCancelBtn = document.getElementById("profileNameCancelBtn");
const profileNameError = document.getElementById("profileNameError");
const profileDossierName = document.getElementById("profileDossierName");
const profileDossierEmail = document.getElementById("profileDossierEmail");
const profileProvider = document.getElementById("profileProvider");
const profileEmailVerified = document.getElementById("profileEmailVerified");
const profileUid = document.getElementById("profileUid");
const profileCreatedAt = document.getElementById("profileCreatedAt");
const profileLastSignIn = document.getElementById("profileLastSignIn");
const profileProviderCount = document.getElementById("profileProviderCount");

const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const loginEmailBtn = document.getElementById("loginEmailBtn");
const accountStatusPanel = document.getElementById("accountStatusPanel");
const accountStatusEyebrow = document.getElementById("accountStatusEyebrow");
const accountStatusTitle = document.getElementById("accountStatusTitle");
const accountStatusMessage = document.getElementById("accountStatusMessage");
const accountStatusLogoutBtn = document.getElementById("accountStatusLogoutBtn");

const registerEmail = document.getElementById("registerEmail");
const registerPassword = document.getElementById("registerPassword");
const registerSubmitBtn = document.getElementById("registerSubmitBtn");

const goToRegisterBtn = document.getElementById("goToRegisterBtn");
const goToLoginBtn = document.getElementById("goToLoginBtn");

const registerPasswordConfirm =
  document.getElementById("registerPasswordConfirm");

  const toggleLoginPassword =
  document.getElementById("toggleLoginPassword");

const toggleRegisterPassword =
  document.getElementById("toggleRegisterPassword");

const toggleRegisterPasswordConfirm =
  document.getElementById("toggleRegisterPasswordConfirm");

const authLoadingOverlay =
  document.getElementById("authLoadingOverlay");

const loginError = document.getElementById("loginError");
const registerError = document.getElementById("registerError");

const discoverPage = document.getElementById("discoverPage");
const aboutPage = document.getElementById("aboutPage");
const openTrustFromLogin = document.getElementById("openTrustFromLogin");

const homeNavBtn = document.getElementById("homeNavBtn");
const homeTabBtn = document.getElementById("homeTabBtn");
const discoverTabBtn = document.getElementById("discoverTabBtn");
const savesTabBtn = document.getElementById("savesTabBtn");
const aboutBtn = document.getElementById("aboutBtn");
const createBtn = document.getElementById("createBtn");

const navAvatarBtn = document.getElementById("navAvatarBtn");
const navAvatar = document.getElementById("navAvatar");
const globalSearchInput = document.getElementById("globalSearchInput");
const globalSearchToggle = document.getElementById("globalSearchToggle");
const mobileHomeBtn = document.getElementById("mobileHomeBtn");
const mobileDiscoverBtn = document.getElementById("mobileDiscoverBtn");
const mobileHistoryBtn = document.getElementById("mobileHistoryBtn");
const mobileCreateBtn = document.getElementById("mobileCreateBtn");

const discoverSearchInput = document.getElementById("discoverSearchInput");
const discoverModeFilter = document.getElementById("discoverModeFilter");
const discoverRefreshBtn = document.getElementById("discoverRefreshBtn");
const discoverStatus = document.getElementById("discoverStatus");
const discoverWorldGrid = document.getElementById("discoverWorldGrid");
const discoverEmptyState = document.getElementById("discoverEmptyState");
const discoverTotalCount = document.getElementById("discoverTotalCount");
const discoverAdventureCount = document.getElementById("discoverAdventureCount");
const discoverNovelCount = document.getElementById("discoverNovelCount");

const communityWorlds = [];
const creatorWorlds = [
  {
    id: "sunless-realm",
    title: "The Sunless Realm",
    mode: "Adventure",
    description:
      "A cursed kingdom where the sun vanished thirty years ago and every lantern is fed by memory.",
    image:
      "linear-gradient(90deg, rgba(0,0,0,.78), rgba(0,0,0,.28)), url('./assets/world-sunless-realm.png')",
    worldSeed:
      "Dạ Thành – vương quốc nơi mặt trời không mọc ba mươi năm. Ánh sáng duy nhất từ đèn đốt bằng ký ức con người. Mỗi giờ đèn sáng, một mảnh ký ức cháy. Giàu có trăm đèn, nghèo có một. Trẻ em bị lấy ký ức tuổi thơ để thắp sáng dinh thự. Hội Đồng Đèn gồm bảy lão nhân không còn ký ức nhưng thấy mọi thứ qua đèn của người khác. Lời đồn: có một ngọn đèn vĩnh cửu dưới Khu Không Tên, nuôi bằng ký ức cả một dân tộc đã mất."},
  {
    id: "memory-market",
    title: "The Memory Market",
    mode: "Novel",
    description:
      "A city where memories are bottled, traded, stolen, and used as currency.",
    image:
      "linear-gradient(135deg, rgba(10,12,18,.3), rgba(0,0,0,.7)), url('./assets/world-memory.png')",
    worldSeed:
      "Ở rìa một đế quốc đang mục ruỗng tồn tại Đại Thư Viện Tro Tàn, nơi lưu giữ những cuốn sách ghi lại các tương lai chưa từng xảy ra. Mỗi cuốn sách là một khả thể vỡ vụn: có cuốn kể về ngày đế quốc sụp đổ dưới chân đội quân cỏ dại biết đi, có cuốn tả một triều đại hoàng kim chưa bao giờ bắt đầu, lại có cuốn chỉ vỏn vẹn một câu: 'Ngươi đã chết ở trang kế tiếp.' Sách không được viết bằng mực – chúng được kết tinh từ tro của những sinh vật đã từng mơ thấy tương lai đó. Muốn đọc một cuốn, ngươi phải đốt nó. Khói sẽ cuộn thành hình ảnh, nhưng mỗi lần đốt là một lần tương lai ấy vĩnh viễn biến mất khỏi thế giới khả thể, và một mảnh tro mới rơi xuống nền thư viện. Đại Thư Viện Tro Tàn có kích thước vô định – hành lang cứ dài ra khi ngươi bước, giá sách mọc lên từ sàn đá bazan như rừng cột, và trần nhà cao đến nỗi không ngọn đèn dầu nào chạm tới bóng tối. Ở đây không có ngày đêm, chỉ có những chiếc đèn lồng bằng xương người treo lủng lẳng, thắp sáng bằng mỡ của những kẻ dám ở lại quá lâu. Ai cai quản thư viện? Không ai biết. Nhưng có lưu truyền một thỏa thuận ngầm: mỗi vị khách chỉ được phép đọc đúng một cuốn sách, rồi phải ra đi. Đọc cuốn thứ hai, ngươi sẽ nghe thấy tiếng lật trang từ phía sau cột sách – nhưng không có ai ở đó. Đọc cuốn thứ ba, ngươi sẽ thấy khuôn mặt của chính mình in trên trang trắng, miệng mấp máy những lời chưa từng thốt ra. Và nếu ngươi đọc đến cuốn thứ tư, Đại Thư Viện sẽ giữ ngươi lại – không phải làm thủ thư, mà làm một cuốn sách mới, xếp vào kệ sâu nhất, nơi những tương lai tăm tối nhất nằm chờ. Đế quốc mục ruỗng bên ngoài, người ta đồn rằng có những kẻ lùng sục đến tận rìa đất chỉ để tìm đến Đại Thư Viện. Họ gọi nhau là 'Những Kẻ Mượn Hy Vọng' – những kẻ ngàn năm trước đã đánh mất tương lai thật của mình, nay lang thang từ bản thảo này sang bản thảo khác, cố tìm một cái kết có hậu để cướp lấy làm của riêng. Nhưng sách ở đây không cho phép cướp. Chúng chỉ cho phép cháy. Và tro sau khi đọc rơi xuống sàn, sẽ tự bốc lên xếp thành một cuốn sách mới – nhưng lần này ba dòng đầu tiên luôn là chính xác những gì ngươi vừa trả giá để thấy. Một số học giả điên khùng cho rằng Đại Thư Viện không phải là một tòa nhà, mà là một vết thương trong cấu trúc thời gian. Mỗi lần ai đó đốt một cuốn sách, họ đang cắt đi một nhánh của cây khả thể, và nhánh ấy quay ngược lại đâm vào thực tại, tạo ra những nghịch lý mà đế quốc mục ruỗng kia gọi là 'dịch bệnh ký ức'. Bệnh ấy khiến người ta nhớ về những thứ chưa hề xảy ra: một cuộc hôn nhân chưa từng diễn ra, một cái chết đã xảy ra theo ba cách khác nhau, một người bạn thời thơ ấu chưa từng tồn tại nhưng ai cũng khóc khi nhắc tên. Đế quốc đổ lỗi cho Đại Thư Viện và đã ba lần sai quân đội đến thiêu rụi nó. Cả ba lần, binh lính trở về với khuôn mặt trắng bệch, không nhớ mình đã thấy gì, chỉ lẩm bẩm: 'Chúng tôi đã đốt rất nhiều sách. Nhưng chúng tôi không nhớ nổi chữ nào. Và khi nhìn vào tay nhau, lòng bàn tay mỗi người đều có một vết tro đen hình chữ 'xin lỗi'.' Ngày nay, không ai dám đến gần rìa đế quốc nữa, trừ những kẻ tuyệt vọng nhất – người mất tình yêu, người mất ý nghĩa, và người đã thấy tương lai thật của mình và không thể chịu nổi. Đối với họ, Đại Thư Viện Tro Tàn là khởi đầu và cũng là kết thúc. Bước qua cánh cổng không cánh, họ thì thầm: 'Xin cho tôi một tương lai khác.' Và một cuốn sách bằng tro sẽ từ từ đông đặc trên giá gần nhất, tự mở ra, những trang giấy đen mịn, chữ khói bốc lên, đợi bàn tay run rẩy cầm lấy diêm.",
  },
  {
    id: "ashen-archive",
    title: "The Ashen Archive",
    mode: "Novel",
    description:
      "A forbidden library records futures that have not happened yet.",
    image:
      "linear-gradient(135deg, rgba(10,12,18,.3), rgba(0,0,0,.7)), url('./assets/world-archive.png')",
    worldSeed:
      "Ở rìa một đế quốc đang mục ruỗng tồn tại Đại Thư Viện Tro Tàn, nơi lưu giữ những cuốn sách ghi lại các tương lai chưa từng xảy ra. Mỗi cuốn sách là một khả thể vỡ vụn: có cuốn kể về ngày đế quốc sụp đổ dưới chân đội quân cỏ dại biết đi, có cuốn tả một triều đại hoàng kim chưa bao giờ bắt đầu, lại có cuốn chỉ vỏn vẹn một câu: 'Ngươi đã chết ở trang kế tiếp.' Sách không được viết bằng mực – chúng được kết tinh từ tro của những sinh vật đã từng mơ thấy tương lai đó. Muốn đọc một cuốn, ngươi phải đốt nó. Khói sẽ cuộn thành hình ảnh, nhưng mỗi lần đốt là một lần tương lai ấy vĩnh viễn biến mất khỏi thế giới khả thể, và một mảnh tro mới rơi xuống nền thư viện. Đại Thư Viện Tro Tàn có kích thước vô định – hành lang cứ dài ra khi ngươi bước, giá sách mọc lên từ sàn đá bazan như rừng cột, và trần nhà cao đến nỗi không ngọn đèn dầu nào chạm tới bóng tối. Ở đây không có ngày đêm, chỉ có những chiếc đèn lồng bằng xương người treo lủng lẳng, thắp sáng bằng mỡ của những kẻ dám ở lại quá lâu. Ai cai quản thư viện? Không ai biết. Nhưng có lưu truyền một thỏa thuận ngầm: mỗi vị khách chỉ được phép đọc đúng một cuốn sách, rồi phải ra đi. Đọc cuốn thứ hai, ngươi sẽ nghe thấy tiếng lật trang từ phía sau cột sách – nhưng không có ai ở đó. Đọc cuốn thứ ba, ngươi sẽ thấy khuôn mặt của chính mình in trên trang trắng, miệng mấp máy những lời chưa từng thốt ra. Và nếu ngươi đọc đến cuốn thứ tư, Đại Thư Viện sẽ giữ ngươi lại – không phải làm thủ thư, mà làm một cuốn sách mới, xếp vào kệ sâu nhất, nơi những tương lai tăm tối nhất nằm chờ. Đế quốc mục ruỗng bên ngoài, người ta đồn rằng có những kẻ lùng sục đến tận rìa đất chỉ để tìm đến Đại Thư Viện. Họ gọi nhau là 'Những Kẻ Mượn Hy Vọng' – những kẻ ngàn năm trước đã đánh mất tương lai thật của mình, nay lang thang từ bản thảo này sang bản thảo khác, cố tìm một cái kết có hậu để cướp lấy làm của riêng. Nhưng sách ở đây không cho phép cướp. Chúng chỉ cho phép cháy. Và tro sau khi đọc rơi xuống sàn, sẽ tự bốc lên xếp thành một cuốn sách mới – nhưng lần này ba dòng đầu tiên luôn là chính xác những gì ngươi vừa trả giá để thấy. Một số học giả điên khùng cho rằng Đại Thư Viện không phải là một tòa nhà, mà là một vết thương trong cấu trúc thời gian. Mỗi lần ai đó đốt một cuốn sách, họ đang cắt đi một nhánh của cây khả thể, và nhánh ấy quay ngược lại đâm vào thực tại, tạo ra những nghịch lý mà đế quốc mục ruỗng kia gọi là 'dịch bệnh ký ức'. Bệnh ấy khiến người ta nhớ về những thứ chưa hề xảy ra: một cuộc hôn nhân chưa từng diễn ra, một cái chết đã xảy ra theo ba cách khác nhau, một người bạn thời thơ ấu chưa từng tồn tại nhưng ai cũng khóc khi nhắc tên. Đế quốc đổ lỗi cho Đại Thư Viện và đã ba lần sai quân đội đến thiêu rụi nó. Cả ba lần, binh lính trở về với khuôn mặt trắng bệch, không nhớ mình đã thấy gì, chỉ lẩm bẩm: 'Chúng tôi đã đốt rất nhiều sách. Nhưng chúng tôi không nhớ nổi chữ nào. Và khi nhìn vào tay nhau, lòng bàn tay mỗi người đều có một vết tro đen hình chữ 'xin lỗi'.' Ngày nay, không ai dám đến gần rìa đế quốc nữa, trừ những kẻ tuyệt vọng nhất – người mất tình yêu, người mất ý nghĩa, và người đã thấy tương lai thật của mình và không thể chịu nổi. Đối với họ, Đại Thư Viện Tro Tàn là khởi đầu và cũng là kết thúc. Bước qua cánh cổng không cánh, họ thì thầm: 'Xin cho tôi một tương lai khác.' Và một cuốn sách bằng tro sẽ từ từ đông đặc trên giá gần nhất, tự mở ra, những trang giấy đen mịn, chữ khói bốc lên, đợi bàn tay run rẩy cầm lấy diêm.",
  },
  {
    id: "hollow-sea",
    title: "The Hollow Sea",
    mode: "Adventure",
    description:
      "An ocean without water, filled with drifting ships and voices beneath the sand.",
    image:
      "linear-gradient(135deg, rgba(10,12,18,.3), rgba(0,0,0,.7)), url('./assets/world-hollow-sea.PNG')",
    worldSeed:
      "Biển Rỗng là một đại dương không còn nước, chỉ còn cát đen, xác tàu trôi lơ lửng và những giọng nói vọng lên từ lòng đất. Cát đen nóng bỏng vào ban ngày và lạnh cắt da ban đêm, biết bám chặt lấy bất cứ ai đi chân trần và kéo họ xuống. Những xác tàu đủ loại – từ thuyền buồm cổ đến tàu chiến bọc thép – mọc lên từ cát như bộ xương, một số lơ lửng cách mặt đất vài sải tay nhờ từ trường dị thường. Giọng nói dưới lòng đất có thể là của người thân đã khuất hoặc của chính bạn trong tương lai, và mỗi lần bạn trả lời, chúng lại rõ hơn một chút. Sinh vật bản địa duy nhất là 'bóng cát' – những thực thể vô hình chỉ lộ ra khi đèn lồng bão tắt, và 'dây leo mộng' mọc từ xác chết bên trong tàu đắm, thứ nước nhầy từ dây leo có thể thay thế nước uống nhưng khiến người dùng mơ thấy đáy biển cũ. Nơi trú ẩn cuối cùng của con người là Xác Tàu Song Hỷ – một con tàu bọc đồng nằm nghiêng, được hàn dính bằng tôn và xương cá voi, bên trong có chợ đen, bar và những kẻ săn giọng nói. Phía nam nơi những con tàu mới nhất nằm, cát mỏng dần và lộ ra một vực thẳm tối om, từ đó có mùi muối và tiếng sóng xa xăm – nhưng không ai quay lại được sau khi bước qua mép vực.",
  },
];

const originalsGrid = document.getElementById("originalsGrid");
const novelWorldsGrid = document.getElementById("novelWorldsGrid");

const featuredTitle = document.getElementById("featuredTitle");
const featuredDescription = document.getElementById("featuredDescription");
const featuredStartBtn = document.getElementById("featuredStartBtn");
const heroNextBtn = document.getElementById("heroNextBtn");

creatorWorlds.length = 0;
let novelWorlds = [];

const createModeModal =
  document.getElementById("createModeModal");

const closeCreateModalBtn =
  document.getElementById("closeCreateModalBtn");

const createAdventureBtn =
  document.getElementById("createAdventureBtn");

const createNovelBtn =
  document.getElementById("createNovelBtn");

const aboutCreateBtn = document.getElementById("aboutCreateBtn");
const aboutHomeBtn = document.getElementById("aboutHomeBtn");
const aboutFinalCreateBtn = document.getElementById("aboutFinalCreateBtn");
const trustBackToLoginBtn = document.getElementById("trustBackToLoginBtn");
const trustHomeBtn = document.getElementById("trustHomeBtn");

const saveSearchInput = document.getElementById("saveSearchInput");
const saveModeFilter = document.getElementById("saveModeFilter");
const saveSortSelect = document.getElementById("saveSortSelect");
const clearSavesSearchBtn = document.getElementById("clearSavesSearchBtn");
const refreshSavesBtn = document.getElementById("refreshSavesBtn");
const savePreviewPanel = document.getElementById("savePreviewPanel");
const savesTotalCount = document.getElementById("savesTotalCount");
const savesAdventureCount = document.getElementById("savesAdventureCount");
const savesNovelCount = document.getElementById("savesNovelCount");
const savesLatestDate = document.getElementById("savesLatestDate");

const avatarDropdown = document.getElementById("avatarDropdown");

const dropdownAvatar = document.getElementById("dropdownAvatar");
const dropdownUserName = document.getElementById("dropdownUserName");
const dropdownUserEmail = document.getElementById("dropdownUserEmail");

const dropdownProfileBtn = document.getElementById("dropdownProfileBtn");
const dropdownLogoutBtn = document.getElementById("dropdownLogoutBtn");

const presetDetailPage = document.getElementById("presetDetailPage");
const presetDetailHero = document.getElementById("presetDetailHero");
const presetDetailMode = document.getElementById("presetDetailMode");
const presetDetailTitle = document.getElementById("presetDetailTitle");
const presetDetailDescription = document.getElementById("presetDetailDescription");
const presetDetailTags = document.getElementById("presetDetailTags");
const presetDetailLore = document.getElementById("presetDetailLore");

const backToHomeFromPreset = document.getElementById("backToHomeFromPreset");
const startPresetWorldBtn = document.getElementById("startPresetWorldBtn");
const previewPresetSeedBtn = document.getElementById("previewPresetSeedBtn");

const adventurePrevBtn = document.getElementById("adventurePrevBtn");
const adventureNextBtn = document.getElementById("adventureNextBtn");
const adventureStepLabel = document.getElementById("adventureStepLabel");

const summaryPlayerName = document.getElementById("summaryPlayerName");
const summaryGender = document.getElementById("summaryGender");
const summaryPersonality = document.getElementById("summaryPersonality");
const summaryStoryStyle = document.getElementById("summaryStoryStyle");
const summaryAdventureOrigin = document.getElementById("summaryAdventureOrigin");
const summaryAdventureGoal = document.getElementById("summaryAdventureGoal");
const summaryAdventureRisk = document.getElementById("summaryAdventureRisk");
const summaryAdventureSeed = document.getElementById("summaryAdventureSeed");
let currentAdventureStep = 0;
const totalAdventureSteps = 8;

const foundationModeBadge = document.getElementById("foundationModeBadge");
const foundationPlayerBadge = document.getElementById("foundationPlayerBadge");
const foundationToneBadge = document.getElementById("foundationToneBadge");

const foundationCharacterName = document.getElementById("foundationCharacterName");
const foundationCharacterGender = document.getElementById("foundationCharacterGender");
const foundationCharacterPersonality = document.getElementById("foundationCharacterPersonality");
const foundationCharacterStyle = document.getElementById("foundationCharacterStyle");
const foundationAdventureOrigin = document.getElementById("foundationAdventureOrigin");
const foundationAdventureGoal = document.getElementById("foundationAdventureGoal");
const foundationAdventureRisk = document.getElementById("foundationAdventureRisk");
const foundationAdventureSeed = document.getElementById("foundationAdventureSeed");
const foundationSurvivalDanger = document.getElementById("foundationSurvivalDanger");
const foundationSurvivalSupplies = document.getElementById("foundationSurvivalSupplies");
const foundationSurvivalWounds = document.getElementById("foundationSurvivalWounds");
const foundationSurvivalTime = document.getElementById("foundationSurvivalTime");

const saveStoryFromGame = document.getElementById("saveStoryFromGame");
const gameSaveStatus = document.getElementById("gameSaveStatus");
const backToLandingFromSetup = document.getElementById("backToLandingFromSetup");

const previewPlayerName = document.getElementById("previewPlayerName");
const previewGender = document.getElementById("previewGender");
const previewPersonality = document.getElementById("previewPersonality");
const previewStoryStyle = document.getElementById("previewStoryStyle");
const previewAdventureOrigin = document.getElementById("previewAdventureOrigin");
const previewAdventureGoal = document.getElementById("previewAdventureGoal");
const previewAdventureRisk = document.getElementById("previewAdventureRisk");
const previewAdventureSeed = document.getElementById("previewAdventureSeed");

const adventureQuestHud = document.getElementById("adventureQuestHud");
const questHudHero = document.getElementById("questHudHero");
const questHudStyle = document.getElementById("questHudStyle");
const questHudOrigin = document.getElementById("questHudOrigin");
const questHudGoal = document.getElementById("questHudGoal");
const questHudRisk = document.getElementById("questHudRisk");
const questHudWounds = document.getElementById("questHudWounds");
const questHudTime = document.getElementById("questHudTime");
const questHudLoadout = document.getElementById("questHudLoadout");

const adventureProgressItems = document.querySelectorAll(
  "#setupPage .adventure-dossier-progress [data-progress]"
);
let novelSessionId = "";
let novelWorldDraft = "";
let novelQuestions = [];
let novelAnswers = [];
let currentNovelQuestionIndex = 0;
let cachedSessions = [];
const savePreviewCache = new Map();
let activePreviewSessionId = "";
let featuredWorldIndex = 0;
let selectedPresetWorld = null;
let worldCatalogLoaded = false;
let worldCatalogLoading = false;
let worldCatalogError = "";
const READER_PREFS_KEY = "aiStoryReaderPrefs";
const readerPrefs = {
  focus: false,
  fontScale: 1,
  lineScale: 1,
};

let pendingOpeningMessage = "";
let pendingChoices = [];
let sessionId = sessionStorage.getItem("session_id") || "";
let currentSessionIsSaved = sessionStorage.getItem("session_is_saved") !== "false";
let currentSessionTitle = sessionStorage.getItem("session_title") || "";
let isRequesting = false;
let isGuest = false;
let avatarCloseTimer = null;
let loadingLoreInterval = null;
let worldLoreInterval = null;
const AI_RETRY_BASE_DELAY_MS = 1800;
const AI_RETRY_MAX_DELAY_MS = 20000;
const RETRY_CANCELLED_CODE = "ai-flow/cancelled";
const loadingPhaseProfiles = {
  default: {
    eyebrow: "AI Flow",
    title: "Opening the AI realm",
    copy: "The AI is weaving together lands, memories, and the fate that awaits you...",
    hint: "Waiting for the AI realm to open.",
  },
  "adventure-start": {
    eyebrow: "Survival Run",
    title: "Opening the expedition",
    copy: "Your route, supplies, threat, and survival pressure are being forged into a live run.",
    hint: "Starting the world with the live backend.",
  },
  "novel-world": {
    eyebrow: "Novel World",
    title: "Building your novel world",
    copy: "The AI is shaping locations, conflicts, mysteries, and the questions that define the novel.",
    hint: "Waiting for the world draft and question wizard.",
  },
  "novel-foundation": {
    eyebrow: "Novel Foundation",
    title: "Writing your foundation",
    copy: "Your character dossier and world answers are becoming the opening foundation.",
    hint: "Preparing the novel session with the real AI response.",
  },
  turn: {
    eyebrow: "Story Turn",
    title: "Waiting for the next scene",
    copy: "Your direction has been sent. The AI is writing the next beat of the story.",
    hint: "Choices and composer stay paused to prevent duplicate turns.",
  },
  "firebase-clock": {
    eyebrow: "Firebase Auth",
    title: "Firebase needs your device time",
    copy: "Your login token could not be refreshed cleanly.",
    hint: "Check your computer date and time, enable automatic time sync, then retry Firebase.",
  },
};
const loadingState = {
  active: false,
  context: "default",
  startedAt: 0,
  attempt: 1,
  retryCount: 0,
  cancelled: false,
  runId: 0,
  elapsedTimer: null,
  retryTimer: null,
  cancelResolver: null,
  retryNowResolver: null,
  abortController: null,
  waitUntil: 0,
};
let currentSessionMode = "adventure";
const ADVENTURE_STYLE_LIMIT = 200;
const adventureQuestState = {
  playerName: "",
  gender: "",
  personality: "",
  storyStyle: "",
  origin: "",
  goal: "",
  risk: "",
  startingCondition: "",
  role: "",
  region: "",
  objective: "",
  threat: "",
  loadout: "",
  danger: 3,
  supplies: 3,
  wounds: 0,
  timePressure: 3,
  lastSurvivalNote: "",
  seed: "",
  isSavedSession: false,
};
if (sessionId) sessionLabel.textContent = sessionId;

// ── Particle canvas ───────────────────────────────────────────────────────────

const THREE_MODULE_URL =
  "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";
let portalSceneController = null;
let pendingPortalPageId = document.body.dataset.page || "landingPage";
let pendingPortalMode = currentSessionMode;
let pendingPortalPulse = 0;

function getPortalProfile(pageId = pendingPortalPageId) {
  if (pageId === "foundationPage") {
    return {
      opacity: 0.92,
      ringOpacity: 0.62,
      particleOpacity: 0.52,
      scale: 1.14,
      speed: 0.34,
      z: 4.8,
      y: -0.04,
      hueShift: 0.16,
    };
  }

  if (pageId === "gamePage") {
    return {
      opacity: 0.78,
      ringOpacity: 0.48,
      particleOpacity: 0.44,
      scale: 0.92,
      speed: 0.24,
      z: 5.8,
      y: 0.1,
      hueShift: 0.02,
    };
  }

  return {
    opacity: 0.34,
    ringOpacity: 0.24,
    particleOpacity: 0.24,
    scale: 0.74,
    speed: 0.12,
    z: 6.6,
    y: 0.18,
    hueShift: 0,
  };
}

function setPortalPage(pageId, mode = currentSessionMode) {
  pendingPortalPageId = pageId || "default";
  pendingPortalMode = mode || "adventure";
  document.body.dataset.portal = pendingPortalPageId;
  portalSceneController?.setPage(pendingPortalPageId, pendingPortalMode);
}

function pulsePortal(strength = 0.8) {
  if (portalSceneController) {
    portalSceneController.pulse(strength);
    return;
  }

  pendingPortalPulse = Math.min(2.2, pendingPortalPulse + strength);
}

async function initPortalScene() {
  const canvas = document.getElementById("particleCanvas");
  const reducedMotionQuery = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  );
  const smallScreenQuery = window.matchMedia("(max-width: 760px)");

  if (!canvas) return;

  if (reducedMotionQuery.matches) {
    canvas.classList.add("portal-canvas-disabled");
    return;
  }

  let THREE;

  try {
    THREE = await import(THREE_MODULE_URL);
  } catch (error) {
    console.warn("Three.js portal could not load.", error);
    canvas.classList.add("portal-canvas-disabled");
    return;
  }

  if (!canvas.isConnected || reducedMotionQuery.matches) return;

  try {
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: !smallScreenQuery.matches,
      powerPreference: "high-performance",
    });

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(44, 1, 0.1, 100);
    const portalGroup = new THREE.Group();
    const ringGroup = new THREE.Group();
    const particleGroup = new THREE.Group();
    const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
    const state = {
      pageId: pendingPortalPageId,
      mode: pendingPortalMode,
      pulse: 0,
      scroll: 0,
      profile: getPortalProfile(pendingPortalPageId),
      current: getPortalProfile(pendingPortalPageId),
      rafId: 0,
      running: true,
    };

    const baseGold = new THREE.Color("#ffd980");
    const baseViolet = new THREE.Color("#9b6cff");
    const memoryGold = baseGold.clone();
    const portalViolet = baseViolet.clone();
    const ember = new THREE.Color("#ff8c69");
    const softWhite = new THREE.Color("#f0e8ff");
    const ringMaterials = [];
    const particleMaterials = [];

    scene.add(portalGroup);
    portalGroup.add(ringGroup);
    portalGroup.add(particleGroup);

    [
      { radius: 1.58, tube: 0.012, color: memoryGold, opacity: 0.54, z: 0 },
      { radius: 1.92, tube: 0.009, color: portalViolet, opacity: 0.34, z: -0.16 },
      { radius: 2.24, tube: 0.006, color: ember, opacity: 0.24, z: -0.32 },
    ].forEach((config, index) => {
      const geometry = new THREE.TorusGeometry(
        config.radius,
        config.tube,
        smallScreenQuery.matches ? 8 : 12,
        smallScreenQuery.matches ? 96 : 160
      );
      const material = new THREE.MeshBasicMaterial({
        color: config.color,
        transparent: true,
        opacity: config.opacity,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const ring = new THREE.Mesh(geometry, material);

      ring.position.z = config.z;
      ring.rotation.x = index % 2 ? 0.12 : -0.08;
      ring.rotation.y = index % 2 ? -0.2 : 0.16;
      ringMaterials.push(material);
      ringGroup.add(ring);
    });

    const coreMaterial = new THREE.MeshBasicMaterial({
      color: portalViolet,
      transparent: true,
      opacity: 0.12,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const core = new THREE.Mesh(
      new THREE.CircleGeometry(1.28, 96),
      coreMaterial
    );
    core.position.z = -0.42;
    ringMaterials.push(coreMaterial);
    ringGroup.add(core);

    const makeParticleField = (count, radius, depth, color, size, opacity) => {
      const positions = new Float32Array(count * 3);

      for (let i = 0; i < count; i += 1) {
        const angle = Math.random() * Math.PI * 2;
        const spread = Math.sqrt(Math.random()) * radius;
        const spiral = (i / count) * Math.PI * 8;

        positions[i * 3] =
          Math.cos(angle + spiral * 0.08) * spread +
          (Math.random() - 0.5) * 0.18;
        positions[i * 3 + 1] =
          Math.sin(angle + spiral * 0.08) * spread * 0.72 +
          (Math.random() - 0.5) * 0.18;
        positions[i * 3 + 2] = (Math.random() - 0.5) * depth;
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute(
        "position",
        new THREE.BufferAttribute(positions, 3)
      );

      const material = new THREE.PointsMaterial({
        color,
        size,
        transparent: true,
        opacity,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        sizeAttenuation: true,
      });

      const points = new THREE.Points(geometry, material);
      particleMaterials.push(material);
      particleGroup.add(points);

      return points;
    };

    const particleScale = smallScreenQuery.matches ? 0.42 : 1;
    const nearParticles = makeParticleField(
      Math.floor((smallScreenQuery.matches ? 220 : 620) * particleScale),
      3.7,
      3.8,
      memoryGold,
      smallScreenQuery.matches ? 0.028 : 0.022,
      0.48
    );
    const farParticles = makeParticleField(
      Math.floor((smallScreenQuery.matches ? 180 : 520) * particleScale),
      5.8,
      6.4,
      portalViolet,
      smallScreenQuery.matches ? 0.02 : 0.017,
      0.3
    );

    const resize = () => {
      const width = window.innerWidth || 1;
      const height = window.innerHeight || 1;
      const pixelRatio = Math.min(
        window.devicePixelRatio || 1,
        smallScreenQuery.matches ? 1.15 : 1.65
      );

      renderer.setPixelRatio(pixelRatio);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    const applyProfile = (pageId, mode) => {
      state.pageId = pageId || "default";
      state.mode = mode || "adventure";
      state.profile = getPortalProfile(state.pageId);
    };

    const onPointerMove = (event) => {
      const intensity = smallScreenQuery.matches ? 0.22 : 0.48;
      pointer.tx =
        ((event.clientX / Math.max(window.innerWidth, 1)) - 0.5) * intensity;
      pointer.ty =
        ((event.clientY / Math.max(window.innerHeight, 1)) - 0.5) * intensity;
    };

    const onScroll = () => {
      state.scroll = window.scrollY || 0;
    };

    const onReducedMotionChange = () => {
      if (reducedMotionQuery.matches) {
        state.running = false;
        cancelAnimationFrame(state.rafId);
        renderer.clear();
        canvas.classList.add("portal-canvas-disabled");
      } else if (!state.running) {
        state.running = true;
        canvas.classList.remove("portal-canvas-disabled");
        animate();
      }
    };

    const animate = () => {
      if (!state.running) return;

      const time = performance.now() * 0.001;
      const target = state.profile;
      const smooth = 0.045;

      state.current.opacity += (target.opacity - state.current.opacity) * smooth;
      state.current.ringOpacity +=
        (target.ringOpacity - state.current.ringOpacity) * smooth;
      state.current.particleOpacity +=
        (target.particleOpacity - state.current.particleOpacity) * smooth;
      state.current.scale += (target.scale - state.current.scale) * smooth;
      state.current.speed += (target.speed - state.current.speed) * smooth;
      state.current.z += (target.z - state.current.z) * smooth;
      state.current.y += (target.y - state.current.y) * smooth;
      state.current.hueShift +=
        (target.hueShift - state.current.hueShift) * smooth;

      pointer.x += (pointer.tx - pointer.x) * 0.035;
      pointer.y += (pointer.ty - pointer.y) * 0.035;
      state.pulse *= 0.92;

      const pulseLift = Math.min(state.pulse, 1.4);
      const pageBoost =
        state.pageId === "foundationPage" || state.pageId === "gamePage"
          ? 1
          : 0.55;

      portalGroup.visible = state.current.opacity > 0.025;
      portalGroup.position.x = pointer.x * pageBoost;
      portalGroup.position.y =
        state.current.y -
        pointer.y * pageBoost +
        Math.sin(time * 0.32) * 0.025;
      portalGroup.position.z = -0.4;
      portalGroup.scale.setScalar(state.current.scale + pulseLift * 0.035);
      portalGroup.rotation.x = pointer.y * 0.16;
      portalGroup.rotation.y = pointer.x * 0.18;
      ringGroup.rotation.z += 0.002 + state.current.speed * 0.004;
      ringGroup.rotation.x = Math.sin(time * 0.22) * 0.055;
      particleGroup.rotation.z -= 0.0008 + state.current.speed * 0.0016;
      particleGroup.rotation.y = Math.sin(time * 0.18) * 0.07;
      nearParticles.rotation.z += 0.0008 + state.current.speed * 0.001;
      farParticles.rotation.z -= 0.0005 + state.current.speed * 0.0008;

      ringMaterials.forEach((material, index) => {
        material.opacity =
          state.current.ringOpacity *
            (index === ringMaterials.length - 1 ? 0.32 : 1 - index * 0.18) +
          pulseLift * 0.08;
      });

      particleMaterials.forEach((material, index) => {
        material.opacity =
          state.current.particleOpacity * (index ? 0.72 : 1) +
          pulseLift * 0.045;
      });

      memoryGold.lerpColors(baseGold, ember, state.current.hueShift);
      portalViolet.lerpColors(
        baseViolet,
        softWhite,
        state.current.hueShift * 0.35
      );
      ringMaterials[0]?.color.copy(memoryGold);
      ringMaterials[1]?.color.copy(portalViolet);
      ringMaterials[2]?.color.copy(ember);
      ringMaterials[3]?.color.copy(portalViolet);
      particleMaterials[0]?.color.copy(memoryGold);
      particleMaterials[1]?.color.copy(portalViolet);

      camera.position.x = pointer.x * 0.24;
      camera.position.y = -pointer.y * 0.22 + state.scroll * 0.000035;
      camera.position.z = state.current.z;
      camera.lookAt(0, 0, 0);

      if (!document.hidden) {
        renderer.render(scene, camera);
      }
      state.rafId = requestAnimationFrame(animate);
    };

    portalSceneController = {
      setPage: applyProfile,
      pulse(strength = 0.8) {
        state.pulse = Math.min(2.2, state.pulse + strength);
      },
      destroy() {
        state.running = false;
        cancelAnimationFrame(state.rafId);
        window.removeEventListener("resize", resize);
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("scroll", onScroll);
        reducedMotionQuery.removeEventListener?.(
          "change",
          onReducedMotionChange
        );
        renderer.dispose();
      },
    };

    resize();
    applyProfile(pendingPortalPageId, pendingPortalMode);
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    reducedMotionQuery.addEventListener?.("change", onReducedMotionChange);
    canvas.classList.add("portal-canvas-ready");
    animate();

    if (pendingPortalPulse) {
      portalSceneController.pulse(pendingPortalPulse);
      pendingPortalPulse = 0;
    }
  } catch (error) {
    console.warn("Three.js portal could not initialize.", error);
    canvas.classList.add("portal-canvas-disabled");
  }
}

initPortalScene();

// ── Page navigation ───────────────────────────────────────────────────────────

const ALL_PAGES = [
  loginPage,
  registerPage,
  forgotPasswordPage,
  verifyEmailPage,
  landingPage,
  presetDetailPage,
  discoverPage,
  profilePage,
  aboutPage,
  trustPage,
  setupPage,
  novelWorldPage,
  novelQuestionPage,
  novelCharacterPage,
  foundationPage,
  gamePage,
  continuePage,
].filter(Boolean);

const reducedMotionMedia = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
);
const smallMotionMedia = window.matchMedia("(max-width: 760px)");
let immersiveMotionContext = null;
let immersiveMotionFrame = null;

function getActivePage() {
  return document.querySelector(".page.active");
}

function getMotionApi() {
  const gsapApi = window.gsap;
  const ScrollTriggerApi = window.ScrollTrigger;

  if (!gsapApi || !ScrollTriggerApi) {
    return null;
  }

  gsapApi.registerPlugin(ScrollTriggerApi);

  return {
    gsap: gsapApi,
    ScrollTrigger: ScrollTriggerApi,
  };
}

function clearImmersiveMotion() {
  if (immersiveMotionFrame) {
    cancelAnimationFrame(immersiveMotionFrame);
    immersiveMotionFrame = null;
  }

  if (immersiveMotionContext) {
    immersiveMotionContext.revert();
    immersiveMotionContext = null;
  }
}

function queueImmersiveMotionRefresh(page = getActivePage()) {
  if (immersiveMotionFrame) {
    cancelAnimationFrame(immersiveMotionFrame);
  }

  immersiveMotionFrame = requestAnimationFrame(() => {
    immersiveMotionFrame = requestAnimationFrame(() => {
      immersiveMotionFrame = null;
      initImmersiveMotion(page || getActivePage());
    });
  });
}

function revealWithoutMotion(page) {
  page
    ?.querySelectorAll(
      ".about-reveal, .world-card, .home-section, .preset-lore-section"
    )
    .forEach((element) => {
      element.classList.add("visible");
      element.style.removeProperty("opacity");
      element.style.removeProperty("transform");
      element.style.removeProperty("visibility");
    });
}

function initImmersiveMotion(page = getActivePage()) {
  clearImmersiveMotion();

  if (!page || !page.classList.contains("active")) return;

  const motionApi = getMotionApi();
  const reducedMotion = reducedMotionMedia.matches;
  const smallScreen = smallMotionMedia.matches;

  if (!motionApi || reducedMotion) {
    revealWithoutMotion(page);
    return;
  }

  const { gsap, ScrollTrigger } = motionApi;

  immersiveMotionContext = gsap.context(() => {
    if (page === landingPage) {
      initHomeMotion(gsap, ScrollTrigger, smallScreen);
    }

    if (page === presetDetailPage) {
      initPresetDetailMotion(gsap, ScrollTrigger, smallScreen);
    }

    if (page === aboutPage) {
      initAboutMotion(gsap, ScrollTrigger, smallScreen);
    }
  }, page);

  ScrollTrigger.refresh();
}

function initHomeMotion(gsap, ScrollTrigger, smallScreen) {
  const hero = document.querySelector(".home-hero");
  const heroContent = document.querySelector(".home-hero-content");
  const heroLayers = gsap.utils.toArray(".home-cosmic-layer");
  const sections = gsap.utils.toArray(".home-section");
  const cards = gsap.utils.toArray(".world-card");

  if (heroContent) {
    gsap.fromTo(
      heroContent,
      { autoAlpha: 0, y: smallScreen ? 16 : 48 },
      { autoAlpha: 1, y: 0, duration: 0.9, ease: "power3.out" }
    );
  }

  if (hero && !smallScreen) {
    gsap.to(hero, {
      backgroundPosition: "center 62%",
      ease: "none",
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "bottom top",
        scrub: 0.8,
      },
    });

    if (heroContent) {
      gsap.to(heroContent, {
        y: -86,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 0.9,
        },
      });
    }

    heroLayers.forEach((layer, index) => {
      gsap.to(layer, {
        y: [-70, -116, -158][index] || -90,
        rotate: [-8, 12, -16][index] || 8,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 1 + index * 0.2,
        },
      });
    });
  }

  sections.forEach((section) => {
    const heading = section.querySelector(".section-heading");
    if (!heading) return;

    gsap.fromTo(
      heading,
      { autoAlpha: 0, y: 32 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: {
          trigger: section,
          start: "top 82%",
          once: true,
        },
      }
    );
  });

  if (cards.length) {
    gsap.set(cards, {
      autoAlpha: 0,
      y: smallScreen ? 22 : 44,
      scale: smallScreen ? 1 : 0.96,
    });

    ScrollTrigger.batch(cards, {
      start: "top 88%",
      once: true,
      onEnter: (batch) => {
        gsap.to(batch, {
          autoAlpha: 1,
          y: 0,
          scale: 1,
          duration: 0.7,
          stagger: 0.08,
          ease: "power3.out",
        });
      },
    });
  }
}

function initPresetDetailMotion(gsap, ScrollTrigger, smallScreen) {
  const hero = document.querySelector(".preset-detail-hero");
  const content = document.querySelector(".preset-detail-content");
  const layers = gsap.utils.toArray(".preset-cosmic-layer");
  const lore = document.querySelector(".preset-lore-section");
  const tags = gsap.utils.toArray(".preset-detail-tags span");

  if (content) {
    gsap.fromTo(
      content,
      { autoAlpha: 0, y: smallScreen ? 18 : 58 },
      { autoAlpha: 1, y: 0, duration: 0.9, ease: "power3.out" }
    );
  }

  if (tags.length) {
    gsap.fromTo(
      tags,
      { autoAlpha: 0, y: 14 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.45,
        stagger: 0.06,
        ease: "power2.out",
        delay: 0.18,
      }
    );
  }

  if (hero && !smallScreen) {
    gsap.to(hero, {
      backgroundPosition: "center 64%",
      ease: "none",
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "bottom top",
        scrub: 0.85,
      },
    });

    layers.forEach((layer, index) => {
      gsap.to(layer, {
        y: [-92, -148][index] || -100,
        rotate: [-10, 16][index] || 8,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 1 + index * 0.25,
        },
      });
    });

    if (content) {
      gsap.to(content, {
        y: -72,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 0.9,
        },
      });
    }
  }

  if (lore) {
    gsap.fromTo(
      lore,
      { autoAlpha: 0, y: 44 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.75,
        ease: "power3.out",
        scrollTrigger: {
          trigger: lore,
          start: "top 84%",
          once: true,
        },
      }
    );
  }
}

function initAboutMotion(gsap, ScrollTrigger, smallScreen) {
  const hero = document.querySelector(".about-v2-hero");
  const heroBg = document.querySelector(".about-v2-hero-bg");
  const heroContent = document.querySelector(".about-v2-hero-content");
  const orbits = gsap.utils.toArray(".about-v2-orbit");
  const revealBlocks = gsap.utils.toArray(".about-reveal");
  const storyCards = gsap.utils.toArray(
    ".about-mode-tab-btn, .about-v2-steps article, .ai-comparison-panel, .about-memory-card, .faq-item"
  );

  revealBlocks.forEach((block) => block.classList.remove("visible"));

  if (heroContent) {
    gsap.fromTo(
      heroContent,
      { autoAlpha: 0, y: smallScreen ? 18 : 54 },
      { autoAlpha: 1, y: 0, duration: 0.9, ease: "power3.out" }
    );
  }

  if (hero && !smallScreen) {
    if (heroBg) {
      gsap.to(heroBg, {
        y: -110,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 1,
        },
      });
    }

    orbits.forEach((orbit, index) => {
      gsap.to(orbit, {
        y: [-120, -70][index] || -90,
        x: [40, -36][index] || 24,
        rotate: [30, -24][index] || 16,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 1 + index * 0.25,
        },
      });
    });
  }

  revealBlocks.forEach((block) => {
    gsap.fromTo(
      block,
      { autoAlpha: 0, y: smallScreen ? 22 : 48 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.75,
        ease: "power3.out",
        scrollTrigger: {
          trigger: block,
          start: "top 82%",
          once: true,
        },
      }
    );
  });

  if (storyCards.length) {
    gsap.fromTo(
      storyCards,
      { autoAlpha: 0, y: 30 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.65,
        stagger: 0.05,
        ease: "power3.out",
        scrollTrigger: {
          trigger: ".about-v2-modes-container",
          start: "top 82%",
          once: true,
        },
      }
    );
  }
}

reducedMotionMedia.addEventListener?.("change", () => {
  queueImmersiveMotionRefresh();
});

smallMotionMedia.addEventListener?.("change", () => {
  queueImmersiveMotionRefresh();
});

function showPage(page) {
  ALL_PAGES.forEach((p) => {
    p.classList.remove("active");
  });

  if (!page) {
    console.error("showPage received null page");
    return;
  }

  page.classList.add("active");

  document.body.dataset.page = page.id;
  setPortalPage(page.id, currentSessionMode);

  if (page === landingPage) {
    requestAnimationFrame(() => {
      renderHomeWorlds();
      renderFeaturedWorld();
      queueImmersiveMotionRefresh(page);
    });
  } else {
    queueImmersiveMotionRefresh(page);
  }

  if (page === novelCharacterPage) {
    updateNovelCharacterPreview();
  }

  if (page === gamePage) {
    applyReaderPrefs();
    resizeComposer();
    requestAnimationFrame(() => {
      updateScrollFade();
    });
  }

  if (page === profilePage) {
    updateProfilePage();
  }

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

function setActiveNav(activeBtn) {
  const navButtons = [
    homeTabBtn,
    discoverTabBtn,
    savesTabBtn,
    mobileHomeBtn,
    mobileDiscoverBtn,
    mobileHistoryBtn,
    mobileCreateBtn,
  ];

  navButtons.forEach((btn) => {
    btn?.classList.remove("active");
    btn?.setAttribute("aria-current", "false");
  });

  activeBtn?.classList.add("active");

  let activeMobileBtn = null;
  let activeDesktopBtn = null;

  if (activeBtn === homeTabBtn || activeBtn === mobileHomeBtn) {
    activeDesktopBtn = homeTabBtn;
    activeMobileBtn = mobileHomeBtn;
  } else if (activeBtn === discoverTabBtn || activeBtn === mobileDiscoverBtn) {
    activeDesktopBtn = discoverTabBtn;
    activeMobileBtn = mobileDiscoverBtn;
  } else if (activeBtn === savesTabBtn || activeBtn === mobileHistoryBtn) {
    activeDesktopBtn = savesTabBtn;
    activeMobileBtn = mobileHistoryBtn;
  } else if (activeBtn === mobileCreateBtn) {
    activeMobileBtn = mobileCreateBtn;
  }

  [activeDesktopBtn, activeMobileBtn].forEach((btn) => {
    btn?.classList.add("active");
    btn?.setAttribute("aria-current", "page");
  });
}

function closeGlobalSearch() {
  document.body.classList.remove("mobile-search-open");
  globalSearchToggle?.setAttribute("aria-expanded", "false");
}

function toggleGlobalSearch() {
  const isOpen = document.body.classList.toggle("mobile-search-open");
  globalSearchToggle?.setAttribute("aria-expanded", String(isOpen));

  if (isOpen) {
    requestAnimationFrame(() => {
      globalSearchInput?.focus();
    });
  }
}

function syncActiveNavToCurrentPage() {
  if (document.body.dataset.page === "landingPage") {
    setActiveNav(homeTabBtn);
  } else if (document.body.dataset.page === "discoverPage") {
    setActiveNav(discoverTabBtn);
  } else if (document.body.dataset.page === "continuePage") {
    setActiveNav(savesTabBtn);
  } else {
    setActiveNav(null);
  }
}

function resetGameInput() {
  if (customAction) {
    customAction.value = "";
    resizeComposer();
  }

  setComposerStatus("");
}

function getSessionSavedFlag(session) {
  if (!session || !Object.prototype.hasOwnProperty.call(session, "is_saved")) {
    return true;
  }

  return session.is_saved !== false;
}

function setCurrentSessionSaved(isSaved, { persist = true } = {}) {
  currentSessionIsSaved = Boolean(isSaved);

  if (persist && sessionId) {
    sessionStorage.setItem(
      "session_is_saved",
      currentSessionIsSaved ? "true" : "false"
    );
  }

  if (!sessionId) {
    sessionStorage.removeItem("session_is_saved");
  }

  updateManualSaveUI();
}

function setCurrentSessionTitle(title = "", { persist = true } = {}) {
  currentSessionTitle = String(title || "").trim();

  if (persist && sessionId && currentSessionTitle) {
    sessionStorage.setItem("session_title", currentSessionTitle);
  }

  if (!sessionId || !currentSessionTitle) {
    sessionStorage.removeItem("session_title");
  }
}

function clearCurrentSessionReference() {
  sessionId = "";
  sessionStorage.removeItem("session_id");
  sessionStorage.removeItem("session_is_saved");
  sessionStorage.removeItem("session_title");
  currentSessionIsSaved = false;
  currentSessionTitle = "";

  if (sessionLabel) {
    sessionLabel.textContent = "Not Started Yet";
  }

  updateManualSaveUI();
}

function getDefaultStoryTitle() {
  if (currentSessionTitle) return currentSessionTitle;

  const playerName =
    adventureQuestState.playerName ||
    novelPlayerName?.value.trim() ||
    auth.currentUser?.displayName ||
    "";

  return playerName ? `${playerName}'s Story` : "Untitled Story";
}

function hasUnsavedDraftSession() {
  return Boolean(sessionId && currentSessionIsSaved === false);
}

function setManualSaveStatus(message = "", isError = false) {
  [foundationSaveStatus, gameSaveStatus].forEach((status) => {
    if (!status) return;

    status.textContent = message;
    status.classList.toggle("error", Boolean(isError));
  });
}

function updateManualSaveUI({ busy = false } = {}) {
  const hasSession = Boolean(sessionId);
  const isSaved = hasSession && currentSessionIsSaved;
  const label = busy ? "Saving..." : isSaved ? "Saved" : "Save";
  const status = !hasSession
    ? "No active story"
    : isSaved
      ? "Saved to History"
      : "Draft not in History";

  [saveStoryFromFoundation, saveStoryFromGame].forEach((btn) => {
    if (!btn) return;

    btn.textContent = label;
    btn.disabled = !hasSession || isSaved || busy || isRequesting;
    btn.classList.toggle("saved", Boolean(isSaved));
  });

  setManualSaveStatus(status);
}

function storyTitleDialog({
  title = "Name this story",
  copy = "Choose a title before saving it to History.",
  defaultTitle = "",
  confirmLabel = "Save",
} = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "confirm-overlay story-title-overlay";
    overlay.innerHTML = `
      <div class="confirm-box story-title-box">
        <p class="eyebrow">History</p>
        <h3>${escapeHtml(title)}</h3>
        <p class="story-title-copy">${escapeHtml(copy)}</p>
        <label class="story-title-field">
          <span>Title</span>
          <input
            class="story-title-input"
            type="text"
            maxlength="120"
            value="${escapeHtml(defaultTitle)}"
            autocomplete="off"
          />
        </label>
        <p class="story-title-error" aria-live="polite"></p>
        <div class="confirm-actions story-title-actions">
          <button class="ghost story-title-cancel" type="button">Cancel</button>
          <button class="primary-btn story-title-confirm" type="button">${escapeHtml(confirmLabel)}</button>
        </div>
      </div>`;

    const input = overlay.querySelector(".story-title-input");
    const error = overlay.querySelector(".story-title-error");
    const confirm = overlay.querySelector(".story-title-confirm");

    const close = (value) => {
      overlay.remove();
      resolve(value);
    };

    const validate = () => {
      const value = input.value.trim();

      if (!value) {
        error.textContent = "Title is required.";
        input.classList.add("field-invalid");
        return null;
      }

      if (value.length > 120) {
        error.textContent = "Title must be 120 characters or fewer.";
        input.classList.add("field-invalid");
        return null;
      }

      error.textContent = "";
      input.classList.remove("field-invalid");
      return value;
    };

    document.body.appendChild(overlay);
    requestAnimationFrame(() => {
      overlay.classList.add("visible");
      input?.focus();
      input?.select();
    });

    confirm?.addEventListener("click", () => {
      const value = validate();
      if (value) close(value);
    });

    overlay.querySelector(".story-title-cancel")?.addEventListener("click", () => {
      close(null);
    });

    input?.addEventListener("input", () => {
      error.textContent = "";
      input.classList.remove("field-invalid");
    });

    input?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        confirm?.click();
      }

      if (event.key === "Escape") {
        event.preventDefault();
        close(null);
      }
    });
  });
}

function upsertCachedSession(session) {
  if (!session?.session_id) return;

  const index = cachedSessions.findIndex(
    (item) => item.session_id === session.session_id
  );

  if (index >= 0) {
    cachedSessions[index] = session;
  } else {
    cachedSessions.unshift(session);
  }

  const previewData = savePreviewCache.get(session.session_id);
  if (previewData?.session) {
    previewData.session = session;
    savePreviewCache.set(session.session_id, previewData);
  }

  if (activePreviewSessionId === session.session_id && previewData) {
    renderSavePreview(previewData);
  }

  renderSavedSessions();
  updateSavesStats();
}

async function saveCurrentSessionToHistory() {
  if (!sessionId) {
    setManualSaveStatus("No active story to save.", true);
    return false;
  }

  if (currentSessionIsSaved) {
    updateManualSaveUI();
    return true;
  }

  const title = await storyTitleDialog({
    title: "Save this story",
    copy: "Give this draft a title before it appears in History.",
    defaultTitle: getDefaultStoryTitle(),
    confirmLabel: "Save to History",
  });

  if (!title) {
    setManualSaveStatus("Draft not in History");
    return false;
  }

  try {
    updateManualSaveUI({ busy: true });

    const data = await requestJson(
      `${API_BASE}/game/sessions/${encodeURIComponent(sessionId)}/save`,
      {
        method: "POST",
        body: JSON.stringify({ title }),
      }
    );
    const savedSession = data?.session || data;

    setCurrentSessionSaved(true);
    setCurrentSessionTitle(savedSession?.title || title);
    setManualSaveStatus("Saved to History");

    upsertCachedSession(savedSession);

    return true;
  } catch (err) {
    console.error(err);
    setManualSaveStatus(err.message || "Could not save this story.", true);
    alert(err.message || String(err));
    return false;
  } finally {
    updateManualSaveUI();
  }
}

async function discardCurrentDraftSession() {
  if (!hasUnsavedDraftSession()) return true;

  const draftSessionId = sessionId;

  try {
    await requestJson(
      `${API_BASE}/game/sessions/${encodeURIComponent(draftSessionId)}`,
      { method: "DELETE" }
    );

    savePreviewCache.delete(draftSessionId);

    if (activePreviewSessionId === draftSessionId) {
      closeSavePreview({ render: false });
    }

    clearCurrentSessionReference();
    if (storyLog) storyLog.innerHTML = "";
    if (choicesBox) choicesBox.innerHTML = "";
    if (customAction) customAction.value = "";
    pendingOpeningMessage = "";
    pendingChoices = [];

    return true;
  } catch (err) {
    console.error(err);
    alert(err.message || String(err));
    return false;
  }
}

function unsavedDraftDialog() {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "confirm-overlay unsaved-draft-overlay";
    overlay.innerHTML = `
      <div class="confirm-box unsaved-draft-box">
        <p class="eyebrow">Unsaved Draft</p>
        <h3>This story is not in History yet.</h3>
        <p class="unsaved-draft-copy">
          Save it before leaving, or discard this draft and continue without saving.
        </p>
        <div class="confirm-actions unsaved-draft-actions">
          <button class="ghost unsaved-cancel" type="button">Cancel</button>
          <button class="danger-btn unsaved-leave" type="button">Leave without saving</button>
          <button class="primary-btn unsaved-save" type="button">Save & Leave</button>
        </div>
      </div>`;

    const finish = (choice) => {
      overlay.remove();
      resolve(choice);
    };

    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("visible"));
    overlay.querySelector(".unsaved-save")?.addEventListener("click", () => finish("save"));
    overlay.querySelector(".unsaved-leave")?.addEventListener("click", () => finish("leave"));
    overlay.querySelector(".unsaved-cancel")?.addEventListener("click", () => finish("cancel"));
  });
}

async function guardUnsavedDraftNavigation(callback) {
  if (!hasUnsavedDraftSession()) {
    await callback?.();
    return true;
  }

  const choice = await unsavedDraftDialog();

  if (choice === "cancel") return false;

  if (choice === "save") {
    const saved = await saveCurrentSessionToHistory();
    if (!saved) return false;
  }

  if (choice === "leave") {
    const discarded = await discardCurrentDraftSession();
    if (!discarded) return false;
  }

  await callback?.();
  return true;
}

updateManualSaveUI();

// ── User UI ───────────────────────────────────────────────────────────────────

let authStatusCheckId = 0;

function showAccountStatusPanel({
  tone = "info",
  eyebrow = "Status",
  title = "Account Notice",
  message = "",
} = {}) {
  if (!accountStatusPanel) return;

  accountStatusPanel.dataset.tone = tone;
  accountStatusPanel.classList.remove("hidden");

  if (accountStatusEyebrow) accountStatusEyebrow.textContent = eyebrow;
  if (accountStatusTitle) accountStatusTitle.textContent = title;
  if (accountStatusMessage) accountStatusMessage.textContent = message;
}

function hideAccountStatusPanel() {
  accountStatusPanel?.classList.add("hidden");
}

async function getAccountStatus() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ACCOUNT_STATUS_TIMEOUT_MS);

  try {
    return await requestJson(`${API_BASE}/account/status`, {
      signal: controller.signal,
    });
  } catch (err) {
    if (err?.name === "AbortError" || err?.cause?.name === "AbortError") {
      throw new Error("Account status check timed out. Please make sure the backend is running.");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

function renderAccountBlock(status = {}) {
  if (status?.maintenance?.enabled) {
    showAccountStatusPanel({
      tone: "maintenance",
      eyebrow: "Maintenance",
      title: "The realm is under maintenance",
      message:
        status.maintenance.message ||
        "AI Story Adventure is under maintenance. Please come back soon.",
    });
    return true;
  }

  if (status?.ban?.enabled) {
    showAccountStatusPanel({
      tone: "banned",
      eyebrow: "Account Restricted",
      title: "This account is banned",
      message: status.ban.message || "This account is banned.",
    });
    return true;
  }

  hideAccountStatusPanel();
  return false;
}

function updateUserUI(user) {
  if (user) {
    // Hide login page if currently visible, go to landing
    if (dropdownUserName) {
      dropdownUserName.textContent =
        user.displayName || "Player";
    }

    if (dropdownUserEmail) {
      dropdownUserEmail.textContent =
        user.email || "";
    }

    if (dropdownAvatar) {
      if (user.photoURL) {
        dropdownAvatar.innerHTML =
          `<img src="${user.photoURL}" alt="avatar" />`;
      } else {
        const initials =
          (user.displayName || user.email || "?")[0].toUpperCase();

        dropdownAvatar.innerHTML =
          `<span>${initials}</span>`;
      }
    }
    if (navAvatar) {
      navAvatar.classList.remove("nav-avatar-empty");

      if (user.photoURL) {
        navAvatar.innerHTML = `<img src="${user.photoURL}" alt="avatar" />`;
      } else {
        const initials = (user.displayName || user.email || "?")[0].toUpperCase();
        navAvatar.innerHTML = `<span>${initials}</span>`;
      }
    }

    // Update user badge
    userBadge?.classList.remove("hidden");
    if (userNameLabel) userNameLabel.textContent = user.displayName || "Người dùng";
    if (userEmailLabel) userEmailLabel.textContent = user.email || "";

    if (userAvatarImg) {
      if (user.photoURL) {
        userAvatarImg.innerHTML = `<img src="${user.photoURL}" alt="avatar" />`;
      } else {
        const initials = (user.displayName || "?")[0].toUpperCase();
        userAvatarImg.innerHTML = `<span>${initials}</span>`;
      }
    }
  } else {
    userBadge?.classList.add("hidden");
    if (userAvatarImg) userAvatarImg.innerHTML = "";
        closeAvatarDropdown();

    if (dropdownUserName) {
      dropdownUserName.textContent = "Guest";
    }

    if (dropdownUserEmail) {
      dropdownUserEmail.textContent = "Not signed in";
    }

    if (dropdownAvatar) {
      dropdownAvatar.innerHTML = `<span>?</span>`;
    }
    // Only redirect to login page if not guest
    if (navAvatar) {
      navAvatar.classList.add("nav-avatar-empty");
      navAvatar.innerHTML = `<span>●</span>`;
    }
    if (!isGuest) {
      showPage(loginPage);
    }
  }

  if (profilePage?.classList.contains("active")) {
    updateProfilePage();
  }
}

// ── Loading state ─────────────────────────────────────────────────────────────

function getLoadingProfile(context = "default") {
  return loadingPhaseProfiles[context] || loadingPhaseProfiles.default;
}

function normalizeLoadingOptions(contextOrOptions = "default") {
  if (typeof contextOrOptions === "string") {
    return { context: contextOrOptions };
  }

  return {
    context: contextOrOptions?.context || "default",
    ...contextOrOptions,
  };
}

function formatLoadingTime(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function updateLoadingElapsed() {
  if (!loadingElapsedText || !loadingState.active) return;

  const waitRemaining = loadingState.waitUntil - Date.now();
  if (waitRemaining > 0) {
    loadingElapsedText.textContent = `Wait ${Math.ceil(waitRemaining / 1000)}s`;
    return;
  }

  const elapsedMs = Date.now() - loadingState.startedAt;
  loadingElapsedText.textContent = formatLoadingTime(elapsedMs);

  if (elapsedMs > 12000 && !loadingState.retryCount && loadingHint) {
    const slowMessage = "Ma thuật đang hội tụ chậm hơn bình thường, xin kiên nhẫn...";
    if (loadingHint.textContent !== slowMessage) {
      loadingHint.textContent = slowMessage;
    }
  }
}

function updateAiLoadingStatus({
  context,
  attempt,
  retryCount,
  title,
  copy,
  hint,
  waitMs,
  showRetryNow = false,
} = {}) {
  const activeContext = context || loadingState.context || "default";
  const profile = getLoadingProfile(activeContext);
  loadingState.context = activeContext;

  if (Number.isFinite(attempt)) loadingState.attempt = attempt;
  if (Number.isFinite(retryCount)) loadingState.retryCount = retryCount;
  loadingState.waitUntil = waitMs ? Date.now() + waitMs : 0;

  loadingOverlay?.setAttribute("data-phase", activeContext);

  if (loadingEyebrow) {
    loadingEyebrow.textContent = profile.eyebrow;
  }

  if (loadingTitle) {
    loadingTitle.textContent = title || profile.title;
  }

  if (worldLoadingText) {
    worldLoadingText.textContent = copy || profile.copy;
    worldLoadingText.style.opacity = 1;
  }

  if (loadingHint) {
    loadingHint.textContent = hint || profile.hint;
  }

  if (loadingRetryText) {
    loadingRetryText.textContent =
      loadingState.retryCount > 0
        ? `Retry ${loadingState.retryCount} - attempt ${loadingState.attempt}`
        : `Attempt ${loadingState.attempt}`;
  }

  retryNowLoadingBtn?.classList.toggle("hidden", !showRetryNow);
  updateLoadingElapsed();
}

function showAiLoading(contextOrOptions = "default") {
  if (!loadingOverlay) return;

  const options = normalizeLoadingOptions(contextOrOptions);
  const isNewRun =
    !loadingState.active || loadingState.context !== options.context;

  if (isNewRun) {
    loadingState.runId += 1;
    loadingState.startedAt = Date.now();
    loadingState.cancelled = false;
    loadingState.attempt = 1;
    loadingState.retryCount = 0;
    loadingState.waitUntil = 0;
  }

  loadingState.active = true;
  loadingState.context = options.context || "default";
  loadingOverlay.classList.remove("hidden");
  updateAiLoadingStatus(options);

  clearInterval(worldLoreInterval);
  worldLoreInterval = setInterval(() => {
    randomizeWorldLoadingText?.();
  }, 2600);

  clearInterval(loadingState.elapsedTimer);
  loadingState.elapsedTimer = setInterval(updateLoadingElapsed, 1000);
}

function hideAiLoading() {
  loadingState.active = false;
  loadingState.cancelled = false;
  loadingState.waitUntil = 0;
  loadingState.cancelResolver = null;
  loadingState.retryNowResolver = null;
  loadingState.abortController = null;

  clearInterval(worldLoreInterval);
  clearInterval(loadingState.elapsedTimer);
  clearTimeout(loadingState.retryTimer);
  worldLoreInterval = null;
  loadingState.elapsedTimer = null;
  loadingState.retryTimer = null;

  loadingOverlay?.classList.add("hidden");
  retryNowLoadingBtn?.classList.add("hidden");
}

function createCancelledError() {
  const err = new Error("Request cancelled.");
  err.name = "RetryCancelledError";
  err.code = RETRY_CANCELLED_CODE;
  return err;
}

function isRetryCancelledError(err) {
  return err?.code === RETRY_CANCELLED_CODE || err?.name === "RetryCancelledError";
}

function cancelCurrentLoading() {
  if (!loadingState.active) return;

  loadingState.cancelled = true;
  loadingState.abortController?.abort();
  loadingState.cancelResolver?.();
  updateAiLoadingStatus({
    hint: "Cancelling this AI request...",
    waitMs: 0,
    showRetryNow: false,
  });
}

function retryCurrentLoadingNow() {
  loadingState.retryNowResolver?.();
}

function setLoading(isLoading, contextOrOptions = "default") {
  isRequesting = isLoading;

  if (rollBtn) rollBtn.disabled = isLoading;
  if (submitBtn) submitBtn.disabled = isLoading;
  if (adventureNextBtn) adventureNextBtn.disabled = isLoading;
  if (createNovelWorldBtn) createNovelWorldBtn.disabled = isLoading;
  if (createNovelFoundationBtn) createNovelFoundationBtn.disabled = isLoading;
  updateManualSaveUI({ busy: false });

  if (isLoading) {
    showAiLoading(contextOrOptions);
  } else {
    hideAiLoading();
  }
}

function setTurnLoading(isLoading, contextOrOptions = "turn") {
  isRequesting = isLoading;

  if (customAction) customAction.disabled = isLoading;
  if (submitBtn) submitBtn.disabled = isLoading;

  submitBtn?.classList.toggle("loading", isLoading);
  document.body.classList.toggle("turn-sending", isLoading);
  setComposerStatus(isLoading ? "Sending your direction..." : "");
  updateManualSaveUI({ busy: false });

  document
    .querySelectorAll(".choice-btn, .novel-choice-card")
    .forEach((btn) => {
      btn.disabled = isLoading;
    });

  if (isLoading) {
    showAiLoading(contextOrOptions);
  } else {
    hideAiLoading();
  }
}

cancelLoadingBtn?.addEventListener("click", cancelCurrentLoading);
retryNowLoadingBtn?.addEventListener("click", retryCurrentLoadingNow);

// ── Story log ─────────────────────────────────────────────────────────────────

function clampReaderValue(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function loadReaderPrefs() {
  try {
    const saved = JSON.parse(localStorage.getItem(READER_PREFS_KEY) || "{}");
    const savedFontScale = Number(saved.fontScale);
    const savedLineScale = Number(saved.lineScale);

    readerPrefs.focus = Boolean(saved.focus);
    readerPrefs.fontScale = Number.isFinite(savedFontScale)
      ? clampReaderValue(savedFontScale, 0, 2)
      : 1;
    readerPrefs.lineScale = Number.isFinite(savedLineScale)
      ? clampReaderValue(savedLineScale, 0, 2)
      : 1;
  } catch {
    readerPrefs.focus = false;
    readerPrefs.fontScale = 1;
    readerPrefs.lineScale = 1;
  }
}

function saveReaderPrefs() {
  try {
    localStorage.setItem(READER_PREFS_KEY, JSON.stringify(readerPrefs));
  } catch {
    // Preferences are optional; the reader still works without storage.
  }
}

function applyReaderPrefs() {
  if (storyLog) {
    storyLog.dataset.fontScale = String(readerPrefs.fontScale);
    storyLog.dataset.lineScale = String(readerPrefs.lineScale);
  }

  document.body.classList.toggle("reader-focus-mode", readerPrefs.focus);

  if (readerFocusToggle) {
    readerFocusToggle.classList.toggle("active", readerPrefs.focus);
    readerFocusToggle.setAttribute("aria-pressed", String(readerPrefs.focus));
  }

  if (readerFontDown) readerFontDown.disabled = readerPrefs.fontScale <= 0;
  if (readerFontUp) readerFontUp.disabled = readerPrefs.fontScale >= 2;
  if (readerLineDown) readerLineDown.disabled = readerPrefs.lineScale <= 0;
  if (readerLineUp) readerLineUp.disabled = readerPrefs.lineScale >= 2;
}

function updateReaderPrefs(partial) {
  Object.assign(readerPrefs, partial);
  readerPrefs.fontScale = clampReaderValue(readerPrefs.fontScale, 0, 2);
  readerPrefs.lineScale = clampReaderValue(readerPrefs.lineScale, 0, 2);
  saveReaderPrefs();
  applyReaderPrefs();
}

function renderProfileAvatar(user) {
  if (!profileAvatar) return;

  if (user?.photoURL) {
    profileAvatar.innerHTML = `<img src="${user.photoURL}" alt="avatar" />`;
    return;
  }

  const initial = (user?.displayName || user?.email || "?")[0].toUpperCase();
  profileAvatar.innerHTML = `<span>${escapeHtml(initial)}</span>`;
}

function getProfileDisplayName(user) {
  return user?.displayName || user?.email?.split("@")[0] || "Player";
}

function formatProfileProviderId(providerId) {
  const providers = {
    "apple.com": "Apple",
    "facebook.com": "Facebook",
    "github.com": "GitHub",
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "password": "Email / Password",
    "phone": "Phone",
    "twitter.com": "Twitter",
  };

  return providers[providerId] || providerId || "Not provided";
}

function getProfileProviders(user) {
  return Array.from(
    new Set(
      (user?.providerData || [])
        .map((providerProfile) => providerProfile?.providerId)
        .filter(Boolean)
    )
  ).map(formatProfileProviderId);
}

function formatProfileDate(value) {
  if (!value) return "Unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Unavailable";

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatProfileUid(uid) {
  if (!uid) return "Unavailable";
  if (uid.length <= 16) return uid;

  return `${uid.slice(0, 6)}...${uid.slice(-6)}`;
}

let isProfileNameEditing = false;

function setProfileNameError(message = "") {
  if (!profileNameError) return;

  profileNameError.textContent = message;
  profileNameError.classList.toggle("visible", Boolean(message));
}

function setProfileNameSaving(isSaving) {
  if (profileNameInput) profileNameInput.disabled = isSaving;
  if (profileNameSaveBtn) {
    profileNameSaveBtn.disabled = isSaving;
    profileNameSaveBtn.textContent = isSaving ? "Saving..." : "Save";
  }
  if (profileNameCancelBtn) profileNameCancelBtn.disabled = isSaving;
  if (profileEditNameBtn) profileEditNameBtn.disabled = isSaving || !auth.currentUser;
}

function setProfileNameEditing(isEditing) {
  isProfileNameEditing = Boolean(isEditing);
  profileNameEditPanel?.classList.toggle("hidden", !isProfileNameEditing);
  profileEditNameBtn?.classList.toggle("hidden", isProfileNameEditing);
  setProfileNameError("");

  if (!isProfileNameEditing) return;

  if (profileNameInput) {
    profileNameInput.value = getProfileDisplayName(auth.currentUser);

    requestAnimationFrame(() => {
      profileNameInput.focus();
      profileNameInput.select();
    });
  }
}

function validateProfileDisplayName(value) {
  const nextName = value.trim();

  if (!nextName) {
    return {
      ok: false,
      message: "Display name is required.",
    };
  }

  if (nextName.length > 50) {
    return {
      ok: false,
      message: "Display name must be 50 characters or fewer.",
    };
  }

  return {
    ok: true,
    value: nextName,
  };
}

async function saveProfileDisplayName() {
  const user = auth.currentUser;

  if (!user) {
    setProfileNameError("Please sign in before editing your profile.");
    return;
  }

  const validation = validateProfileDisplayName(profileNameInput?.value || "");

  if (!validation.ok) {
    setProfileNameError(validation.message);
    return;
  }

  if (validation.value === (user.displayName || "").trim()) {
    setProfileNameEditing(false);
    return;
  }

  setProfileNameSaving(true);
  setProfileNameError("");

  try {
    await updateProfile(user, {
      displayName: validation.value,
    });

    setProfileNameEditing(false);
    updateUserUI(auth.currentUser);
    updateProfilePage();
  } catch (err) {
    console.error(err);
    setProfileNameError(err?.message || "Could not update display name.");
  } finally {
    setProfileNameSaving(false);
  }
}

function updateProfileUser() {
  const user = auth.currentUser;
  const displayName = getProfileDisplayName(user);
  const email = user?.email || (user ? "Not provided" : "Not signed in");
  const providers = getProfileProviders(user);
  const linkedIdentityCount = user?.providerData?.length || 0;

  renderProfileAvatar(user);

  if (profileDisplayName) {
    profileDisplayName.textContent = displayName;
  }

  if (profileEmail) {
    profileEmail.textContent = email;
  }

  if (profileLoginState) {
    profileLoginState.textContent = user
      ? user.emailVerified
        ? "Verified Firebase account"
        : "Firebase account connected"
      : "Not signed in";
  }

  if (profileDossierName) {
    profileDossierName.textContent = user ? displayName : "Not signed in";
  }

  if (profileDossierEmail) {
    profileDossierEmail.textContent = email;
  }

  if (profileProvider) {
    profileProvider.textContent = providers.length
      ? providers.join(", ")
      : user
        ? "Not provided"
        : "Unavailable";
  }

  if (profileEmailVerified) {
    profileEmailVerified.textContent = user
      ? user.emailVerified
        ? "Verified"
        : "Not verified"
      : "Unavailable";
    profileEmailVerified.dataset.state = user
      ? user.emailVerified
        ? "verified"
        : "unverified"
      : "empty";
  }

  if (profileUid) {
    profileUid.textContent = formatProfileUid(user?.uid);
    profileUid.title = user?.uid || "";
  }

  if (profileCreatedAt) {
    profileCreatedAt.textContent = formatProfileDate(user?.metadata?.creationTime);
  }

  if (profileLastSignIn) {
    profileLastSignIn.textContent = formatProfileDate(user?.metadata?.lastSignInTime);
  }

  if (profileProviderCount) {
    profileProviderCount.textContent = user
      ? `${linkedIdentityCount} linked ${linkedIdentityCount === 1 ? "identity" : "identities"}`
      : "Unavailable";
  }

  if (profileEditNameBtn) {
    profileEditNameBtn.disabled = !user;
  }

  if (profileNameInput && !isProfileNameEditing) {
    profileNameInput.value = user ? displayName : "";
  }

  if (!user && isProfileNameEditing) {
    setProfileNameEditing(false);
  }
}

function updateProfilePage() {
  updateProfileUser();
}

function setComposerStatus(message, isError = false) {
  if (!composerStatus) return;

  composerStatus.textContent = message || "";
  composerStatus.classList.toggle("error", Boolean(isError && message));
}

function resizeComposer() {
  if (!customAction) return;

  autoResize(customAction);
}

function scrollStoryToLatest(behavior = "smooth") {
  if (!storyLog) return;

  storyLog.scrollTo({
    top: storyLog.scrollHeight,
    behavior,
  });
  updateScrollFade();
}

function typeMessage(el, text, speed = 13) {
  return new Promise((resolve) => {
    let i = 0;
    el.textContent = "";
    function tick() {
      if (i < text.length) {
        el.textContent += text[i++];
        storyLog.scrollTop = storyLog.scrollHeight;
        setTimeout(tick, speed);
      } else {
        resolve();
      }
    }
    tick();
  });
}

function wrapWordsInSpan(element) {
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
  const textNodes = [];
  let node;
  while (node = walker.nextNode()) {
    textNodes.push(node);
  }
  
  const spanNodes = [];
  textNodes.forEach(textNode => {
    const text = textNode.nodeValue;
    const words = text.split(/(\s+)/);
    const fragment = document.createDocumentFragment();
    words.forEach(word => {
      if (word.trim() === '') {
        fragment.appendChild(document.createTextNode(word));
      } else {
        const span = document.createElement('span');
        span.className = 'streaming-word';
        span.textContent = word;
        span.style.opacity = '0';
        span.style.transition = 'opacity 0.22s ease';
        fragment.appendChild(span);
        spanNodes.push(span);
      }
    });
    textNode.parentNode.replaceChild(fragment, textNode);
  });
  return spanNodes;
}

async function startStreamingReveal(element) {
  const words = wrapWordsInSpan(element);
  let skipAnimation = false;
  
  const skipHandler = () => {
    skipAnimation = true;
  };
  
  document.addEventListener('click', skipHandler);
  document.addEventListener('keydown', skipHandler);
  
  for (let i = 0; i < words.length; i++) {
    if (skipAnimation) {
      for (let j = i; j < words.length; j++) {
        words[j].style.opacity = '1';
      }
      break;
    }
    words[i].style.opacity = '1';
    if (i % 3 === 0) {
      scrollStoryToLatest("auto");
    }
    await new Promise(resolve => setTimeout(resolve, 28));
  }
  
  document.removeEventListener('click', skipHandler);
  document.removeEventListener('keydown', skipHandler);
  scrollStoryToLatest("smooth");
}

async function addMessage(role, content, animate = false) {
  if (!storyLog) return null;

  const isNovel = currentSessionMode === "novel";

  const item = document.createElement("article");

  if (isNovel) {
    item.className =
      role === "user"
        ? "novel-user-direction"
        : "novel-scene";

    if (role === "user") {
      item.innerHTML = `
        <div class="novel-direction-label">Direction</div>
        <p>${escapeHtml(content)}</p>
      `;
    } else {
      const sceneCount =
        storyLog.querySelectorAll(".novel-scene").length + 1;

      item.innerHTML = `
        <div class="novel-scene-label">Scene ${sceneCount}</div>
        <div class="novel-prose">
          ${formatStoryParagraphs(content)}
        </div>
      `;
    }
  } else {
    item.className =
      role === "user"
        ? "message user-message"
        : "message ai-message";

    item.innerHTML = `
      <div class="message-icon">
        ${role === "user" ? "◆" : "✦"}
      </div>
      <div class="message-content">
        ${formatStoryParagraphs(content)}
      </div>
    `;
  }

  storyLog.appendChild(item);
  pulsePortal(role === "ai" ? 0.95 : 0.5);

  item.scrollIntoView({
    behavior: "smooth",
    block: "end",
  });

  if (animate && role === "ai") {
    item.classList.add("message-enter");
    const proseContainer = item.querySelector(".novel-prose") || item.querySelector(".message-content");
    if (proseContainer) {
      await startStreamingReveal(proseContainer);
    }
  }

  updateScrollFade();
  return item;
}

function addChoicesLoading() {
  choicesBox.innerHTML = "";
  const placeholder = document.createElement("div");
  placeholder.className = "choices-loading";
  placeholder.id = "choicesLoading";
  placeholder.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;
  choicesBox.appendChild(placeholder);
}

function removeChoicesLoading() {
  const el = document.getElementById("choicesLoading");
  if (el) el.remove();
}

function updateScrollFade() {
  if (!storyLog) return;

  const distanceFromBottom =
    storyLog.scrollHeight - storyLog.scrollTop - storyLog.clientHeight;
  const hasScrollableContent = storyLog.scrollHeight > storyLog.clientHeight + 8;
  const isNearBottom = distanceFromBottom < 72;

  storyLog.classList.toggle("has-scroll", hasScrollableContent);
  storyLog.classList.toggle("is-near-bottom", isNearBottom);

  if (scrollLatestBtn) {
    scrollLatestBtn.disabled = !hasScrollableContent || isNearBottom;
  }
}
storyLog?.addEventListener("scroll", updateScrollFade);

// ── Auto-resize textarea ──────────────────────────────────────────────────────

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

// ── Ripple ────────────────────────────────────────────────────────────────────

function addRipple(btn, e) {
  const rect = btn.getBoundingClientRect();
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  ripple.style.cssText = `left:${e.clientX - rect.left}px;top:${e.clientY - rect.top}px`;
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
}

// ── API helper ────────────────────────────────────────────────────────────────

function createApiError(message, details = {}) {
  const err = new Error(message || "Request failed");
  Object.assign(err, details);
  return err;
}

function getApiErrorMessage(data) {
  if (typeof data === "string") return data || "Request failed";

  if (data?.detail) {
    return typeof data.detail === "string"
      ? data.detail
      : JSON.stringify(data.detail, null, 2);
  }

  if (data?.message) return data.message;

  if (data?.error) {
    return typeof data.error === "string"
      ? data.error
      : JSON.stringify(data.error, null, 2);
  }

  return "Request failed";
}

function getErrorText(err) {
  return [
    err?.message,
    err?.code,
    err?.status,
    typeof err?.data === "string" ? err.data : "",
    err?.data?.detail,
    err?.data?.message,
    err?.data?.error,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function isFirebaseClockOrTokenError(err) {
  const text = getErrorText(err);
  return (
    err?.isFirebaseAuthError &&
    (
      text.includes("clock") ||
      text.includes("time") ||
      text.includes("token") ||
      text.includes("issued") ||
      text.includes("expired") ||
      text.includes("auth/network-request-failed") ||
      text.includes("network")
    )
  );
}

function isTransientAiError(err) {
  if (isRetryCancelledError(err)) return false;

  const status = Number(err?.status || 0);
  const text = getErrorText(err);

  if ([400, 401, 403, 404, 422].includes(status)) return false;
  if (
    text.includes("validation") ||
    text.includes("not found") ||
    text.includes("permission") ||
    text.includes("unauthorized") ||
    text.includes("forbidden") ||
    text.includes("missing") ||
    text.includes("daily limit") ||
    text.includes("daily turn limit") ||
    text.includes("daily story creation limit") ||
    text.includes("daily create limit") ||
    text.includes("usage limit") ||
    text.includes("turn limit reached") ||
    text.includes("story creation limit reached") ||
    text.includes("not enough points")
  ) {
    return false;
  }

  if (status === 429 || status === 503 || status === 502 || status === 504) {
    return true;
  }

  if (
    text.includes("high demand") ||
    text.includes("overloaded") ||
    text.includes("rate limit") ||
    text.includes("quota") ||
    text.includes("busy") ||
    text.includes("temporarily unavailable") ||
    text.includes("try again later")
  ) {
    return true;
  }

  return (
    !status &&
    (
      err?.name === "TypeError" ||
      text.includes("failed to fetch") ||
      text.includes("networkerror") ||
      text.includes("network request failed")
    )
  );
}

function getRetryDelay(attempt, isFirebaseIssue = false) {
  const base = isFirebaseIssue ? 3200 : AI_RETRY_BASE_DELAY_MS;
  const jitter = Math.floor(Math.random() * 900);
  return Math.min(
    AI_RETRY_MAX_DELAY_MS,
    Math.round(base * Math.pow(1.65, Math.max(0, attempt - 1))) + jitter
  );
}

function waitForRetryDelay(delayMs, runId) {
  return new Promise((resolve, reject) => {
    if (loadingState.cancelled || loadingState.runId !== runId) {
      reject(createCancelledError());
      return;
    }

    const finish = () => {
      clearTimeout(loadingState.retryTimer);
      loadingState.cancelResolver = null;
      loadingState.retryNowResolver = null;
      loadingState.retryTimer = null;
      loadingState.waitUntil = 0;
      resolve();
    };

    loadingState.cancelResolver = () => {
      clearTimeout(loadingState.retryTimer);
      loadingState.cancelResolver = null;
      loadingState.retryNowResolver = null;
      loadingState.retryTimer = null;
      reject(createCancelledError());
    };

    loadingState.retryNowResolver = finish;
    loadingState.retryTimer = setTimeout(finish, delayMs);
  });
}

async function requestJsonWithRetry(url, options = {}, retryOptions = {}) {
  const context = retryOptions.context || "default";

  if (!loadingState.active) {
    showAiLoading(context);
  }

  const runId = loadingState.runId;
  let attempt = 1;

  while (true) {
    if (loadingState.cancelled || loadingState.runId !== runId) {
      throw createCancelledError();
    }

    const controller = new AbortController();
    loadingState.abortController = controller;

    updateAiLoadingStatus({
      context,
      attempt,
      retryCount: Math.max(0, attempt - 1),
      waitMs: 0,
      showRetryNow: false,
    });

    try {
      const data = await requestJson(url, {
        ...options,
        signal: controller.signal,
      });

      if (loadingState.cancelled || loadingState.runId !== runId) {
        throw createCancelledError();
      }

      return data;
    } catch (err) {
      if (
        loadingState.cancelled ||
        loadingState.runId !== runId ||
        err?.name === "AbortError"
      ) {
        throw createCancelledError();
      }

      const firebaseIssue = isFirebaseClockOrTokenError(err);
      const transientIssue = isTransientAiError(err);

      if (!firebaseIssue && !transientIssue) {
        throw err;
      }

      const delayMs = getRetryDelay(attempt, firebaseIssue);
      const retryContext = firebaseIssue ? "firebase-clock" : context;

      updateAiLoadingStatus({
        context: retryContext,
        attempt: attempt + 1,
        retryCount: attempt,
        waitMs: delayMs,
        showRetryNow: firebaseIssue,
        copy: firebaseIssue
          ? "Firebase could not refresh your login token cleanly."
          : "The AI service is busy right now, so the app is holding your place and retrying.",
        hint: firebaseIssue
          ? "Sync your computer clock in system settings, then press Retry Firebase. Cancel will stop this flow."
          : `High demand detected. Retrying automatically in ${Math.ceil(delayMs / 1000)} seconds.`,
      });

      await waitForRetryDelay(delayMs, runId);
      attempt += 1;
    } finally {
      if (loadingState.abortController === controller) {
        loadingState.abortController = null;
      }
    }
  }
}

async function requestJson(url, options = {}) {
  const { skipAuth = false, ...fetchOptions } = options;
  const headers = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers || {}),
  };

  if (!skipAuth) {
    if (!auth.currentUser) {
      showPage(loginPage);
      throw new Error("Phiên đăng nhập đã hết hạn.");
    }

    let token = "";
    try {
      token = await auth.currentUser.getIdToken(true);
    } catch (err) {
      throw createApiError(
        err?.message || "Firebase could not refresh your login token.",
        {
          code: err?.code,
          cause: err,
          isFirebaseAuthError: true,
        }
      );
    }
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  let retries = 1;

  while (true) {
    try {
      response = await fetch(url, {
        ...fetchOptions,
        headers,
      });
    } catch (err) {
      throw createApiError(err?.message || "Network request failed.", {
        cause: err,
        name: err?.name,
        isNetworkError: true,
      });
    }

    const contentType = response.headers.get("content-type") || "";

    const data = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text().catch(() => "");

    if (!response.ok) {
      const errMsg = getApiErrorMessage(data);
      
      // Auto-retry for Firebase clock skew issue
      if (retries > 0 && errMsg && errMsg.includes("Token used too early")) {
        console.warn("Token used too early (clock skew). Retrying in 2s...");
        await sleep(2000);
        
        // Cập nhật lại token mới nếu có thể
        if (auth.currentUser) {
            const newToken = await auth.currentUser.getIdToken(true);
            headers.Authorization = `Bearer ${newToken}`;
        }
        
        retries--;
        continue;
      }

      console.error("API error:", data);
      throw createApiError(errMsg, {
        status: response.status,
        data,
      });
    }

    return data;
  }
}

// ── Ambient pulse ─────────────────────────────────────────────────────────────

function pulseAmbient() {
  document.body?.classList.add("ambient-pulse");
  pulsePortal(
    document.body.dataset.page === "gamePage" ||
      document.body.dataset.page === "foundationPage"
      ? 1.05
      : 0.58
  );

  setTimeout(() => {
    document.body?.classList.remove("ambient-pulse");
  }, 900);
}

// ── Confirm dialog ────────────────────────────────────────────────────────────

function confirmDialog(message) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "confirm-overlay";
    overlay.innerHTML = `
      <div class="confirm-box">
        <p>${message}</p>
        <div class="confirm-actions">
          <button class="ghost confirm-cancel">Cancel</button>
          <button class="danger-btn confirm-ok">Confirm</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("visible"));
    overlay.querySelector(".confirm-ok").addEventListener("click", () => { overlay.remove(); resolve(true); });
    overlay.querySelector(".confirm-cancel").addEventListener("click", () => { overlay.remove(); resolve(false); });
  });
}

// ── Render choices ────────────────────────────────────────────────────────────

function renderChoicesFromArray(choices = []) {
  if (!choicesBox) return;

  choicesBox.innerHTML = "";

  const isNovel = currentSessionMode === "novel";

  choices.forEach((choice, index) => {
    const btn = document.createElement("button");
    btn.type = "button";

    btn.className = isNovel
      ? "novel-choice-card"
      : "choice-btn adventure-choice-card";

    // Staggered reveal animation
    btn.style.animationDelay = `${index * 80}ms`;

    btn.innerHTML = `
      <span class="choice-number">${index + 1}</span>
      <span>${escapeHtml(choice)}</span>
    `;

    btn.addEventListener("click", async () => {
      customAction.value = choice;
      await submitAction(choice);
    });

    choicesBox.appendChild(btn);
  });

  updateScrollFade();
}

async function submitAction(actionText) {
  const action = String(actionText || customAction?.value || "").trim();

  if (!action) {
    setComposerStatus("Write a direction before sending.", true);
    customAction?.focus();
    return;
  }

  if (!sessionId || isRequesting) return;

  const pendingUserMessage = await addMessage("user", action);

  if (customAction) {
    customAction.value = "";
    resizeComposer();
  }

  let turnWasCancelled = false;

  try {
    setTurnLoading(true, "turn");
    addChoicesLoading();

    const data = await requestJsonWithRetry(
      `${API_BASE}/game/turn`,
      {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          player_input: action,
          target_words: getNumberValue(turnTargetWords, 600),
        }),
      },
      { context: "turn" }
    );

    const message = data.message || data.story || "";
    const choices = data.choices || [];
    setCurrentSessionSaved(getSessionSavedFlag(data.session));
    setCurrentSessionTitle(data.session?.title || currentSessionTitle);
    if (currentSessionMode === "adventure") {
      syncAdventureQuestStateFromSession(data.session || {});
    }

    await addMessage("ai", message, true);
    renderChoicesFromArray(choices);
  } catch (err) {
    console.error(err);
    if (isRetryCancelledError(err)) {
      turnWasCancelled = true;
    } else {
      alert(err.message);
    }
  } finally {
    removeChoicesLoading();
    setTurnLoading(false);
    if (turnWasCancelled) {
      pendingUserMessage?.remove();
      if (customAction) {
        customAction.value = action;
        resizeComposer();
      }
      setComposerStatus("AI request cancelled. You can edit and send again.");
    }
    updateScrollFade();
  }
}

// ── Suggestion chips ──────────────────────────────────────────────────────────

document.querySelectorAll(".suggestion-row").forEach((row) => {
  const targetId = row.dataset.target;
  const input = document.getElementById(targetId);
  row.querySelectorAll(".suggestion-chip").forEach((btn) => {
    btn.addEventListener("click", () => { input.value = btn.textContent.trim(); input.focus(); });
  });
});


// ── Novel flow ───────────────────────────────────────────────────────────────

function getNumberValue(input, fallback = 700) {
  const value = Number(input?.value || fallback);
  if (!Number.isFinite(value)) return fallback;
  return Math.min(Math.max(value, 100), 2000);
}

function getNovelTargetWordsValue() {
  const value = Number(novelFoundationTargetWords?.value || 700);

  if (!Number.isFinite(value)) return 700;

  return Math.min(Math.max(Math.round(value), 150), 2000);
}

function clearNovelCharacterErrors() {
  if (novelNameError) novelNameError.textContent = "";
  if (novelTargetWordsError) novelTargetWordsError.textContent = "";
  if (novelCharacterFormError) novelCharacterFormError.textContent = "";

  novelPlayerName?.classList.remove("field-invalid");
  novelFoundationTargetWords?.classList.remove("field-invalid");
}

function updateNovelCharacterPreview() {
  const name = novelPlayerName?.value.trim() || "The Wanderer";
  const gender = novelGender?.value.trim();
  const age = novelAge?.value.trim();
  const occupation = novelOccupation?.value.trim();
  const personality = novelPersonality?.value.trim();
  const targetWords = getNovelTargetWordsValue();
  const savedAnswers = novelAnswers.filter((item) => item?.answer).length;

  if (novelPreviewName) {
    novelPreviewName.textContent = name;
  }

  if (novelPreviewIdentity) {
    const identityParts = [gender, age && `${age} years old`].filter(Boolean);
    novelPreviewIdentity.textContent = identityParts.length
      ? identityParts.join(" / ")
      : "Identity and age will appear here.";
  }

  if (novelPreviewRole) {
    novelPreviewRole.textContent = occupation || "Not defined";
  }

  if (novelPreviewTargetWords) {
    novelPreviewTargetWords.textContent = `${targetWords} words`;
  }

  if (novelPreviewAnswers) {
    novelPreviewAnswers.textContent =
      `${savedAnswers} saved`;
  }

  if (novelPreviewPersonality) {
    novelPreviewPersonality.textContent = personality
      ? truncateText(personality, 260)
      : "Add a personality note to shape the protagonist's voice.";
  }

  if (novelPreviewWorld) {
    novelPreviewWorld.textContent = novelWorldDraft
      ? truncateText(novelWorldDraft, 320)
      : "Your generated world and question answers will guide the opening foundation.";
  }
}

function applyNovelCharacterChip(chip) {
  const field = chip?.dataset.field;
  const value = chip?.dataset.value;

  if (!field || !value) return;

  if (field === "gender" && novelGender) {
    novelGender.value = value;
    novelGender.focus();
  }

  if (field === "occupation" && novelOccupation) {
    novelOccupation.value = value;
    novelOccupation.focus();
  }

  if (field === "personality" && novelPersonality) {
    const current = novelPersonality.value.trim();
    const alreadyUsed = current
      .toLowerCase()
      .split(",")
      .map((item) => item.trim())
      .includes(value.toLowerCase());

    novelPersonality.value = current
      ? alreadyUsed
        ? current
        : `${current}, ${value}`
      : value;
    novelPersonality.focus();
  }

  clearNovelCharacterErrors();
  updateNovelCharacterPreview();
}

function validateNovelCharacterDossier() {
  clearNovelCharacterErrors();

  const playerName = novelPlayerName?.value.trim() || "";
  let targetWords = getNovelTargetWordsValue();

  if (novelFoundationTargetWords) {
    const rawTarget = Number(novelFoundationTargetWords.value || 700);

    if (!Number.isFinite(rawTarget)) {
      targetWords = 700;
      novelFoundationTargetWords.classList.add("field-invalid");
      if (novelTargetWordsError) {
        novelTargetWordsError.textContent =
          "Target words reset to 700.";
      }
    } else if (rawTarget < 150 || rawTarget > 2000) {
      novelFoundationTargetWords.classList.add("field-invalid");
      if (novelTargetWordsError) {
        novelTargetWordsError.textContent =
          "Target words were clamped to 150-2000.";
      }
    }

    novelFoundationTargetWords.value = targetWords;
  }

  if (!playerName) {
    if (novelNameError) {
      novelNameError.textContent = "Name is required.";
    }
    if (novelCharacterFormError) {
      novelCharacterFormError.textContent =
        "Add a protagonist name before creating the novel.";
    }
    novelPlayerName?.classList.add("field-invalid");
    novelPlayerName?.focus();
    updateNovelCharacterPreview();
    return null;
  }

  updateNovelCharacterPreview();

  return {
    playerName,
    gender: novelGender?.value.trim() || null,
    age: novelAge?.value.trim() || null,
    occupation: novelOccupation?.value.trim() || null,
    personality: novelPersonality?.value.trim() || null,
    targetWords,
  };
}

function applySessionMode(mode = "adventure") {
  currentSessionMode = mode || "adventure";
  document.body.dataset.mode = currentSessionMode;
  setPortalPage(document.body.dataset.page, currentSessionMode);
  updateGameplayModeUI();
}

function resetNovelFlow() {
  novelWorldDraft = "";
  novelQuestions = [];
  novelAnswers = [];
  currentNovelQuestionIndex = 0;

  if (novelWorldSeed) novelWorldSeed.value = "";
  if (novelQuestionAnswer) novelQuestionAnswer.value = "";
  if (worldDraftText) worldDraftText.textContent = "";
  if (novelPlayerName) novelPlayerName.value = "";
  if (novelGender) novelGender.value = "";
  if (novelAge) novelAge.value = "";
  if (novelOccupation) novelOccupation.value = "";
  if (novelPersonality) novelPersonality.value = "";
  if (novelFoundationTargetWords) novelFoundationTargetWords.value = 700;

  clearNovelCharacterErrors();
  updateNovelCharacterPreview();
}


function renderNovelQuestion() {
  const question = novelQuestions[currentNovelQuestionIndex];

  if (!question) {
    showPage(novelCharacterPage);
    return;
  }

  if (novelQuestionStepLabel) {
    novelQuestionStepLabel.textContent =
      `Step ${currentNovelQuestionIndex + 1} of ${novelQuestions.length}`;
  }

  if (novelQuestionTitle) {
    novelQuestionTitle.textContent = "Shape Your Novel";
  }

  if (novelQuestionText) {
    novelQuestionText.textContent = question.question || "Question";
  }

  if (novelQuestionAnswer) {
    novelQuestionAnswer.value =
      novelAnswers[currentNovelQuestionIndex]?.answer || "";

    setTimeout(() => novelQuestionAnswer.focus(), 80);
  }

  if (novelQuestionSuggestions) {
    novelQuestionSuggestions.innerHTML = "";

    (question.suggestions || []).forEach((suggestion) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip";
      chip.textContent = suggestion;

      chip.addEventListener("click", () => {
        novelQuestionAnswer.value = suggestion;
        novelQuestionAnswer.focus();
      });

      novelQuestionSuggestions.appendChild(chip);
    });
  }

  if (novelQuestionNextBtn) {
    novelQuestionNextBtn.textContent =
      currentNovelQuestionIndex === novelQuestions.length - 1
        ? "Continue"
        : "Next";
  }

  showPage(novelQuestionPage);
}

function showWorldDraftModal() {
  if (worldDraftText) {
    worldDraftText.textContent = novelWorldDraft || "No world draft yet.";
  }
  worldDraftModal?.classList.remove("hidden");
}

function hideWorldDraftModal() {
  worldDraftModal?.classList.add("hidden");
}

// ══════════════════════════════════════════════ EVENT LISTENERS ══

// Login: Google
loginGoogleBtn?.addEventListener("click", async () => {
  hideAccountStatusPanel();
  clearAuthError(loginError);
  loginGoogleBtn.disabled = true;
  showAuthLoading();
  const loginGoogleText = loginGoogleBtn?.querySelector("span");

    if (loginGoogleText) {
      loginGoogleText.textContent = "Đang đăng nhập...";
    }
  try {
    await Promise.all([
      signInWithPopup(auth, provider),
      sleep(1000),
    ]);
    
  } catch (err) {
    console.error(err);
    showAuthError(loginError, getFriendlyAuthError(err));
  } finally {
    loginGoogleBtn.disabled = false;
    hideAuthLoading();
    if (loginGoogleText) {
      loginGoogleText.textContent = "Tiếp tục với Google";
    }
  }
});

// Login: Guest
guestBtn?.addEventListener("click", async () => {
  hideAccountStatusPanel();
  clearAuthError(loginError);
  guestBtn.disabled = true;
  showAuthLoading();
  try {
    isGuest = true;
    await Promise.all([
      signInAnonymously(auth),
      sleep(1200),
    ]);
  } catch (err) {
    console.error(err);
    isGuest = false;
    showAuthError(loginError, "Could not start Guest mode. Please check your internet connection.");
  } finally {
    guestBtn.disabled = false;
    hideAuthLoading();
  }
});

async function performLogout() {
  try {
    await signOut(auth);
    isGuest = false;
    clearCurrentSessionReference();
    if (storyLog) storyLog.innerHTML = "";
    if (choicesBox) choicesBox.innerHTML = "";
    // onAuthStateChanged will call showPage(loginPage)
  } catch (err) {
    console.error(err);
    showAuthError(loginError, getFriendlyAuthError(err));
  }
}

async function handleLogoutRequest() {
  const confirmed = hasUnsavedDraftSession()
    ? true
    : await confirmDialog("Logout and return to the login screen?");

  if (!confirmed) return;

  await guardUnsavedDraftNavigation(async () => {
    await performLogout();
  });
}

// Logout
logoutBtn?.addEventListener("click", async () => {
  await handleLogoutRequest();
  return;
  const confirmed = await confirmDialog("Đăng xuất? Bạn sẽ trở về màn hình đăng nhập.");
  if (!confirmed) return;
  try {
    await signOut(auth);
    isGuest = false;
    sessionId = "";
    sessionStorage.removeItem("session_id");
    sessionLabel.textContent = "Not Started Yet";
    storyLog.innerHTML = "";
    choicesBox.innerHTML = "";
    // onAuthStateChanged will call showPage(loginPage)
  } catch (err) {
    console.error(err);
    showAuthError(loginError, getFriendlyAuthError(err));
  }
});

// Landing → Setup
accountStatusLogoutBtn?.addEventListener("click", async () => {
  try {
    hideAccountStatusPanel();
    await signOut(auth);
  } catch (err) {
    console.error(err);
    showAuthError(loginError, getFriendlyAuthError(err));
  }
});

goToSetupBtn?.addEventListener("click", () => {
  openAdventureSetup();
});
function openAdventureSetup() {
  currentAdventureStep = 0;
  applySessionMode("adventure");
  renderAdventureStep();
  showPage(setupPage);
  setActiveNav(null);
}
// Landing → Novel World Setup
startNovelBtn?.addEventListener("click", () => {
  resetNovelFlow();
  applySessionMode("novel");
  showPage(novelWorldPage);
});

backToLandingFromNovelWorld?.addEventListener("click", () => showPage(landingPage));


viewWorldDraftBtn?.addEventListener("click", showWorldDraftModal);
closeWorldDraftBtn?.addEventListener("click", hideWorldDraftModal);
worldDraftModal?.addEventListener("click", (event) => {
  if (event.target === worldDraftModal) hideWorldDraftModal();
});

novelQuestionBackBtn?.addEventListener("click", () => {
  const ok = saveCurrentNovelAnswer();

  if (!ok) return;

  if (currentNovelQuestionIndex <= 0) {
    showPage(novelWorldPage);
    return;
  }

  currentNovelQuestionIndex -= 1;
  renderNovelQuestion();
});


backToNovelQuestionsBtn?.addEventListener("click", () => {
  if (novelQuestions.length) renderNovelQuestion();
  else showPage(novelWorldPage);
});

[
  novelPlayerName,
  novelGender,
  novelAge,
  novelOccupation,
  novelPersonality,
  novelFoundationTargetWords,
].forEach((input) => {
  input?.addEventListener("input", () => {
    clearNovelCharacterErrors();
    updateNovelCharacterPreview();
  });
});

novelCharacterChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    applyNovelCharacterChip(chip);
  });
});

createNovelFoundationBtn?.addEventListener("click", async () => {
  if (!sessionId) {
    alert("Please create a novel world first.");
    showPage(novelWorldPage);
    return;
  }

  if (isRequesting) return;

  const characterDossier = validateNovelCharacterDossier();
  if (!characterDossier) return;

  try {
    setLoading(true, "novel-foundation");
    const targetWords = characterDossier.targetWords;

    const data = await requestJsonWithRetry(
      `${API_BASE}/game/novel/foundation`,
      {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          player_name: characterDossier.playerName,
          gender: characterDossier.gender,
          age: characterDossier.age,
          occupation: characterDossier.occupation,
          personality: characterDossier.personality,
          answers: novelAnswers
          .filter((item) => item?.answer)
          .map((item, index) => ({
            question_id: item.question_id || `q${index + 1}`,
            question: item.question || "",
            answer: item.answer || "",
          })),
          target_words: targetWords,
        }),
      },
      { context: "novel-foundation" }
    );

    sessionId = data.session_id;
    sessionStorage.setItem("session_id", sessionId);
    setCurrentSessionSaved(getSessionSavedFlag(data.session));
    setCurrentSessionTitle(data.session?.title || "");
    sessionLabel.textContent = sessionId;
    applySessionMode("novel");
    if (turnTargetWords) turnTargetWords.value = targetWords;

    pendingOpeningMessage = data.message || "";
    pendingChoices = data.choices || [];
    renderFoundationContent(
  data.foundation_text || data.session?.foundation_text || ""
);
updateFoundationSidebar();

    showPage(foundationPage);
    pulseAmbient();
  } catch (err) {
  console.error(err);
  if (!isRetryCancelledError(err)) {
    alert(err.message || String(err));
  }
}
  finally {
    setLoading(false);
  }
});

// Setup → Landing
// Setup → Landing
backToLandingBtn?.addEventListener("click", () => {
  showPage(landingPage);
  setActiveNav(homeTabBtn);
});

backToLandingFromSetup?.addEventListener("click", () => {
  showPage(landingPage);
  setActiveNav(homeTabBtn);
});

// Continue button
continueBtn?.addEventListener("click", async () => {
  showPage(continuePage);
  await loadSessions();
});


// Foundation → Setup
backToSetupBtn?.addEventListener("click", () => {
  if (currentSessionMode === "novel") {
    showPage(novelCharacterPage);
    setActiveNav(null);
    return;
  }

  openAdventureSetup();
});

// Foundation → Game
beginStoryBtn?.addEventListener("click", async () => {
  storyLog.innerHTML = "";
  choicesBox.innerHTML = "";
  applySessionMode(currentSessionMode);
  updateGameplayModeUI();
  showPage(gamePage);
  await addMessage("ai", pendingOpeningMessage, true);
  renderChoicesFromArray(pendingChoices);
  pulseAmbient();
});

saveStoryFromFoundation?.addEventListener("click", async () => {
  await saveCurrentSessionToHistory();
});

saveStoryFromGame?.addEventListener("click", async () => {
  await saveCurrentSessionToHistory();
});

function getInputText(input) {
  return String(input?.value || "").replace(/\s+/g, " ").trim();
}

function clampPlainText(value, limit) {
  const text = String(value || "").replace(/\s+/g, " ").trim();

  if (text.length <= limit) return text;
  if (limit <= 3) return text.slice(0, limit);

  return `${text.slice(0, limit - 3).trimEnd()}...`.slice(0, limit);
}

function buildAdventureStyleSeed(values = {}) {
  const parts = [
    ["Region", values.storyStyle],
    ["Objective", values.origin],
    ["Threat", values.goal],
    ["Loadout", values.risk],
  ].filter(([, value]) => String(value || "").trim());

  if (!parts.length) return "";

  let valueLimit = parts.length > 2 ? 42 : 72;
  let seed = "";

  do {
    seed = parts
      .map(([label, value]) => `${label}: ${clampPlainText(value, valueLimit)}`)
      .join(" | ");
    valueLimit -= 4;
  } while (seed.length > ADVENTURE_STYLE_LIMIT && valueLimit >= 24);

  return clampPlainText(seed, ADVENTURE_STYLE_LIMIT);
}

function clampSurvivalStat(value, fallback = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.min(Math.max(Math.round(number), 0), 5);
}

function buildSurvivalDefaults(values = {}) {
  const combined = [
    values.gender,
    values.personality,
    values.storyStyle,
    values.origin,
    values.goal,
    values.risk,
  ].join(" ").toLowerCase();

  return {
    danger: combined.includes("hunted") || combined.includes("storm") ? 4 : 3,
    supplies: combined.includes("supplies") || combined.includes("medkit") ? 4 : 3,
    wounds: combined.includes("wounded") || combined.includes("injured") ? 1 : 0,
    timePressure: combined.includes("countdown") || combined.includes("dawn") ? 4 : 3,
  };
}

function buildAdventureProfilePayload(questState = adventureQuestState) {
  const clean = (value, fallback, limit = 220) =>
    clampPlainText(String(value || fallback || ""), limit);

  return {
    player_name: clean(questState.playerName, "The Wanderer", 80),
    role: clean(questState.role || questState.personality, "Wanderer", 120),
    starting_condition:
      clean(questState.startingCondition || questState.gender, "Thrown into danger", 160),
    region: clean(questState.region || questState.storyStyle, "Unknown wilds", 220),
    objective:
      clean(questState.objective || questState.origin, "Survive and find a way forward", 220),
    threat: clean(questState.threat || questState.goal, "A danger is closing in", 220),
    loadout: clean(questState.loadout || questState.risk, "Light supplies", 220),
    danger: clampSurvivalStat(questState.danger, 3),
    supplies: clampSurvivalStat(questState.supplies, 3),
    wounds: clampSurvivalStat(questState.wounds, 0),
    time_pressure: clampSurvivalStat(questState.timePressure, 3),
    last_survival_note:
      questState.lastSurvivalNote || "The survival run has just begun.",
  };
}

function syncAdventureQuestStateFromInputs() {
  const values = {
    playerName: getInputText(playerNameInput),
    gender: getInputText(genderInput),
    personality: getInputText(personalityInput),
    storyStyle: getInputText(storyStyleInput),
    origin: getInputText(adventureOriginInput),
    goal: getInputText(adventureGoalInput),
    risk: getInputText(adventureRiskInput),
  };
  const survivalDefaults = buildSurvivalDefaults(values);

  Object.assign(adventureQuestState, values, {
    startingCondition: values.gender,
    role: values.personality,
    region: values.storyStyle,
    objective: values.origin,
    threat: values.goal,
    loadout: values.risk,
    danger: survivalDefaults.danger,
    supplies: survivalDefaults.supplies,
    wounds: survivalDefaults.wounds,
    timePressure: survivalDefaults.timePressure,
    seed: buildAdventureStyleSeed(values),
    isSavedSession: false,
  });

  return adventureQuestState;
}

function syncAdventureQuestStateFromSession(session = {}) {
  const profile = session?.adventure_profile || {};
  Object.assign(adventureQuestState, {
    playerName: profile.player_name || session?.title || "",
    gender: profile.starting_condition || "",
    personality: profile.role || "",
    storyStyle: profile.region || "",
    origin: profile.objective || "",
    goal: profile.threat || "",
    risk: profile.loadout || "",
    startingCondition: profile.starting_condition || "",
    role: profile.role || "",
    region: profile.region || "",
    objective: profile.objective || "",
    threat: profile.threat || "",
    loadout: profile.loadout || "",
    danger: clampSurvivalStat(profile.danger, 3),
    supplies: clampSurvivalStat(profile.supplies, 3),
    wounds: clampSurvivalStat(profile.wounds, 0),
    timePressure: clampSurvivalStat(profile.time_pressure, 3),
    lastSurvivalNote: profile.last_survival_note || "",
    seed: profile.seed || session?.world_seed || "",
    isSavedSession: getSessionSavedFlag(session),
  });

  updateAdventureQuestHud();
}

function displayAdventureValue(value, fallback = "Not defined") {
  return String(value || "").trim() || fallback;
}

function updateAdventureQuestHud() {
  const isAdventure = currentSessionMode === "adventure";

  if (adventureQuestHud) {
    adventureQuestHud.hidden = !isAdventure;
  }

  if (!isAdventure) return;

  const savedFallback = adventureQuestState.isSavedSession
    ? "Not stored for this history item"
    : "Not defined";

  if (questHudHero) {
    questHudHero.textContent =
      adventureQuestState.playerName || "Unknown Hero";
  }

  if (questHudStyle) {
    questHudStyle.textContent = `${clampSurvivalStat(adventureQuestState.danger, 3)}/5`;
  }

  if (questHudOrigin) {
    questHudOrigin.textContent = `${clampSurvivalStat(adventureQuestState.supplies, 3)}/5`;
  }

  if (questHudGoal) {
    questHudGoal.textContent = displayAdventureValue(
      adventureQuestState.objective || adventureQuestState.origin,
      savedFallback
    );
  }

  if (questHudRisk) {
    questHudRisk.textContent = displayAdventureValue(
      adventureQuestState.threat || adventureQuestState.goal,
      savedFallback
    );
  }

  if (questHudWounds) {
    questHudWounds.textContent = `${clampSurvivalStat(adventureQuestState.wounds, 0)}/5`;
  }

  if (questHudTime) {
    questHudTime.textContent = `${clampSurvivalStat(adventureQuestState.timePressure, 3)}/5`;
  }

  if (questHudLoadout) {
    questHudLoadout.textContent = displayAdventureValue(
      adventureQuestState.loadout || adventureQuestState.risk,
      savedFallback
    );
  }
}

// Roll character
async function startAdventureGame() {
  if (!auth.currentUser && !isGuest) {
    showPage(loginPage);
    return;
  }

  if (isRequesting) return;

  try {
    setLoading(true, "adventure-start");
    const questState = syncAdventureQuestStateFromInputs();
    if (!questState.playerName) questState.playerName = "The Wanderer";
    const adventureProfile = buildAdventureProfilePayload(questState);

    const data = await requestJsonWithRetry(
      `${API_BASE}/game/start`,
      {
        method: "POST",
        body: JSON.stringify({
          player_name: questState.playerName || "The Wanderer",
          gender: questState.gender || null,
          personality: questState.personality || null,
          story_style: questState.seed || null,
          character_hint: null,
          adventure_profile: adventureProfile,
        }),
      },
      { context: "adventure-start" }
    );

    sessionId = data.session_id;
    sessionStorage.setItem("session_id", sessionId);
    setCurrentSessionSaved(getSessionSavedFlag(data.session));
    setCurrentSessionTitle(data.session?.title || "");

    currentSessionMode = data.session?.mode || "adventure";
    document.body.dataset.mode = currentSessionMode;
    syncAdventureQuestStateFromSession(data.session || {});

    pendingOpeningMessage = data.message || "";
    pendingChoices = data.choices || [];

    if (sessionLabel) {
      sessionLabel.textContent = sessionId;
    }

    if (foundationText) {
      renderFoundationContent(
  data.foundation_text || data.session?.foundation_text || ""
);
    }

    updateFoundationSidebar();

    showPage(foundationPage);
    pulseAmbient();

  } catch (err) {
    console.error(err);
    if (!isRetryCancelledError(err)) {
      alert(err.message);
    }
  } finally {
    setLoading(false);
  }
}



// New game
newGameBtn?.addEventListener("click", async () => {
  if (hasUnsavedDraftSession()) {
    await guardUnsavedDraftNavigation(async () => {
      applySessionMode("adventure");
      if (storyLog) storyLog.innerHTML = "";
      if (choicesBox) choicesBox.innerHTML = "";
      if (customAction) customAction.value = "";
      showPage(landingPage);
    });
    return;
  }
  const confirmed = await confirmDialog("Bắt đầu game mới? Tiến trình hiện tại sẽ bị xoá.");
  if (!confirmed) return;

  clearCurrentSessionReference();

  applySessionMode("adventure");

  if (storyLog) storyLog.innerHTML = "";
  if (choicesBox) choicesBox.innerHTML = "";
  if (customAction) customAction.value = "";

  showPage(landingPage);
});

// Keyboard shortcut


// ── Session helpers ───────────────────────────────────────────────────────────

async function loadSessions() {
  if (!sessionList) return;

  refreshSavesBtn?.setAttribute("disabled", "true");
  sessionList.innerHTML = `
    <div class="saves-loading glass-panel">
      Loading history...
    </div>
  `;

  try {
    const sessions = await requestJson(`${API_BASE}/game/sessions`);

    cachedSessions = Array.isArray(sessions) ? sessions : [];
    savePreviewCache.clear();
    updateSavesStats();

    if (
      activePreviewSessionId &&
      !cachedSessions.some((session) => session.session_id === activePreviewSessionId)
    ) {
      closeSavePreview({ render: false });
    }

    renderSavedSessions();

  } catch (err) {
    sessionList.innerHTML = `
      <div class="saves-empty glass-panel error-state">
        <h3>Could not load history</h3>
        <p>${escapeHtml(err.message || String(err))}</p>
      </div>
    `;
  } finally {
    refreshSavesBtn?.removeAttribute("disabled");
  }
}

function updateSavesStats() {
  const total = cachedSessions.length;
  const adventureCount = cachedSessions.filter(
    (session) => getSessionMode(session) === "adventure"
  ).length;
  const novelCount = cachedSessions.filter(
    (session) => getSessionMode(session) === "novel"
  ).length;
  const latest = cachedSessions.reduce(
    (max, session) => Math.max(max, getSessionTime(session)),
    0
  );

  if (savesTotalCount) savesTotalCount.textContent = String(total);
  if (savesAdventureCount) savesAdventureCount.textContent = String(adventureCount);
  if (savesNovelCount) savesNovelCount.textContent = String(novelCount);
  if (savesLatestDate) {
    savesLatestDate.textContent = latest
      ? formatSessionDate(new Date(latest).toISOString(), true)
      : "-";
  }
}

function getSessionMode(session) {
  return session?.mode === "novel" ? "novel" : "adventure";
}

function getSessionTime(session) {
  const value = session?.updated_at || session?.created_at || "";
  const time = Date.parse(value);
  return Number.isNaN(time) ? 0 : time;
}

function formatSessionDate(value, compact = false) {
  if (!value) return "Unknown";

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";

  try {
    return date.toLocaleString(
      undefined,
      compact
        ? { month: "short", day: "numeric" }
        : { dateStyle: "medium", timeStyle: "short" }
    );
  } catch {
    return date.toLocaleString();
  }
}

function getSessionPreview(session) {
  return (
    session?.foundation_text ||
    session?.world_summary ||
    session?.story_summary ||
    session?.character_summary ||
    ""
  ).trim();
}

function truncateText(value, limit = 220) {
  const text = String(value || "").replace(/\s+/g, " ").trim();

  if (text.length <= limit) return text;
  return `${text.slice(0, limit).trim()}...`;
}

function getFilteredSavedSessions() {
  const query = saveSearchInput?.value.trim().toLowerCase() || "";
  const modeFilter = saveModeFilter?.value || "all";
  const sortMode = saveSortSelect?.value || "newest";

  const filtered = cachedSessions.filter((session) => {
    const mode = getSessionMode(session);
    const searchable = [
      session?.title,
      session?.session_id,
      mode,
      getSessionPreview(session),
    ]
      .join(" ")
      .toLowerCase();

    const matchesSearch = !query || searchable.includes(query);
    const matchesMode = modeFilter === "all" || mode === modeFilter;

    return matchesSearch && matchesMode;
  });

  return [...filtered].sort((a, b) => {
    if (sortMode === "oldest") return getSessionTime(a) - getSessionTime(b);
    if (sortMode === "title") {
      return (a.title || "Untitled Story").localeCompare(
        b.title || "Untitled Story"
      );
    }
    if (sortMode === "mode") {
      const modeCompare = getSessionMode(a).localeCompare(getSessionMode(b));
      return modeCompare || getSessionTime(b) - getSessionTime(a);
    }

    return getSessionTime(b) - getSessionTime(a);
  });
}

function renderSavedSessions() {
  if (!sessionList) return;

  updateSavesStats();
  const filtered = getFilteredSavedSessions();

  if (!filtered.length) {
    const hasAnySaves = cachedSessions.length > 0;

    sessionList.innerHTML = `
      <div class="saves-empty glass-panel">
        <svg class="empty-state-icon" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="60" cy="60" r="48" stroke="var(--border-accent)" stroke-width="1.5" stroke-dasharray="4 8" opacity="0.6" class="spin-slow"/>
          <path d="M45 40 L75 40 L85 60 L75 80 L45 80 L35 60 Z" stroke="var(--muted)" stroke-width="2" fill="var(--panel-hover)" opacity="0.8"/>
          <circle cx="60" cy="60" r="12" fill="var(--accent)" opacity="0.3"/>
          <circle cx="60" cy="60" r="4" fill="var(--accent)"/>
        </svg>
        <h3>${hasAnySaves ? "No history items match this view" : "No saved stories in History yet"}</h3>
        <p>
          ${
            hasAnySaves
              ? "Adjust the search, mode, or sort controls to reveal more stories."
              : "Start a new Adventure or Novel Mode story, then press Save when you want it to appear here."
          }
        </p>
      </div>
    `;
    return;
  }

  sessionList.innerHTML = "";

  filtered.forEach((session, index) => {
    const card = document.createElement("article");
    card.className = `save-card glass-panel${
      activePreviewSessionId === session.session_id ? " active" : ""
    }`;
    card.style.setProperty("--save-index", String(index));

    const mode = getSessionMode(session);
    const modeLabel =
      mode === "novel" ? "Novel" : "Adventure";

    const preview =
      getSessionPreview(session) ||
      "No story preview available yet.";

    const targetWords = session.target_words
      ? `${session.target_words} words/turn`
      : "Default length";
    const factCount = Array.isArray(session.important_facts)
      ? session.important_facts.length
      : 0;

    card.innerHTML = `
      <div class="save-card-top">
        <span class="save-mode ${mode}">
          ${modeLabel}
        </span>

        <span class="save-date">
          ${escapeHtml(formatSessionDate(session.updated_at))}
        </span>
      </div>

      <h3>${escapeHtml(session.title || "Untitled Story")}</h3>

      <p class="save-card-preview">${escapeHtml(truncateText(preview, 230))}</p>

      <dl class="save-meta-grid">
        <div>
          <dt>Length</dt>
          <dd>${escapeHtml(targetWords)}</dd>
        </div>
        <div>
          <dt>Memory</dt>
          <dd>${factCount} facts</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>${escapeHtml(formatSessionDate(session.created_at, true))}</dd>
        </div>
      </dl>

      <div class="save-card-actions">
        <button
          type="button"
          class="ghost preview-session-btn"
        >
          Preview
        </button>

        <button
          type="button"
          class="ghost rename-session-btn"
        >
          Rename
        </button>

        <button
          type="button"
          class="ghost export-session-btn"
        >
          Export .md
        </button>

        <button
          type="button"
          class="ghost publish-session-btn"
        >
          Publish
        </button>

        <button
          type="button"
          class="primary-btn load-session-btn"
        >
          Continue
        </button>

        <button
          type="button"
          class="danger-btn delete-session-btn"
        >
          Delete
        </button>
      </div>
    `;

    card
      .querySelector(".preview-session-btn")
      ?.addEventListener("click", () => {
        previewSession(session.session_id);
      });

    card
      .querySelector(".publish-session-btn")
      ?.addEventListener("click", () => {
        openPublishModal(session.session_id, session.title);
      });

    card
      .querySelector(".load-session-btn")
      ?.addEventListener("click", () => {
        continueSession(session.session_id);
      });

    card
      .querySelector(".rename-session-btn")
      ?.addEventListener("click", () => {
        renameHistorySession(session.session_id, session.title || "Untitled Story");
      });

    card
      .querySelector(".export-session-btn")
      ?.addEventListener("click", (event) => {
        exportHistorySession(session.session_id, event.currentTarget);
      });

    card
      .querySelector(".delete-session-btn")
      ?.addEventListener("click", () => {
        deleteSession(session.session_id);
      });

    sessionList.appendChild(card);
  });
}

async function renameHistorySession(targetSessionId, currentTitle = "Untitled Story") {
  if (!targetSessionId) return;

  const title = await storyTitleDialog({
    title: "Rename story",
    copy: "Update the title shown in History.",
    defaultTitle: currentTitle,
    confirmLabel: "Save Name",
  });

  if (!title) return;

  try {
    const updatedSession = await requestJson(
      `${API_BASE}/game/sessions/${encodeURIComponent(targetSessionId)}`,
      {
        method: "PATCH",
        body: JSON.stringify({ title }),
      }
    );

    if (sessionId === targetSessionId) {
      setCurrentSessionTitle(updatedSession?.title || title);
    }

    upsertCachedSession(updatedSession);
  } catch (err) {
    console.error(err);
    alert(err.message || String(err));
  }
}

function normalizeMarkdownText(value = "") {
  return String(value || "")
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function sanitizeFilename(value = "story") {
  const safe = String(value || "story")
    .trim()
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
    .replace(/\s+/g, "-")
    .slice(0, 80);

  return safe || "story";
}

function getAdventureProfile(session = {}) {
  return session?.adventure_profile && typeof session.adventure_profile === "object"
    ? session.adventure_profile
    : {};
}

function buildSurvivalMarkdown(session = {}) {
  const profile = getAdventureProfile(session);
  if (!Object.keys(profile).length) return [];

  return [
    "## Survival Run",
    "",
    `- Danger: ${clampSurvivalStat(profile.danger, 3)}/5`,
    `- Supplies: ${clampSurvivalStat(profile.supplies, 3)}/5`,
    `- Wounds: ${clampSurvivalStat(profile.wounds, 0)}/5`,
    `- Time pressure: ${clampSurvivalStat(profile.time_pressure, 3)}/5`,
    `- Objective: ${normalizeMarkdownText(profile.objective || "Not defined")}`,
    `- Threat: ${normalizeMarkdownText(profile.threat || "Not defined")}`,
    `- Loadout: ${normalizeMarkdownText(profile.loadout || "Light supplies")}`,
    `- Last note: ${normalizeMarkdownText(profile.last_survival_note || "None")}`,
    "",
  ];
}

function renderSurvivalPreviewHtml(session = {}) {
  const profile = getAdventureProfile(session);
  if (!Object.keys(profile).length) return "";

  return `
    <section class="save-preview-section survival-preview-section">
      <h3>Survival Run</h3>
      <div class="survival-preview-grid">
        <span>Danger <strong>${clampSurvivalStat(profile.danger, 3)}/5</strong></span>
        <span>Supplies <strong>${clampSurvivalStat(profile.supplies, 3)}/5</strong></span>
        <span>Wounds <strong>${clampSurvivalStat(profile.wounds, 0)}/5</strong></span>
        <span>Time <strong>${clampSurvivalStat(profile.time_pressure, 3)}/5</strong></span>
      </div>
      <p><strong>Objective:</strong> ${escapeHtml(profile.objective || "Not defined")}</p>
      <p><strong>Threat:</strong> ${escapeHtml(profile.threat || "Not defined")}</p>
      <p><strong>Loadout:</strong> ${escapeHtml(profile.loadout || "Light supplies")}</p>
    </section>
  `;
}

function buildHistoryMarkdown(data) {
  const session = data?.session || {};
  const messages = Array.isArray(data?.messages) ? data.messages : [];
  const title = session.title || "Untitled Story";
  const mode = getSessionMode(session);
  const foundation = normalizeMarkdownText(
    data?.foundation_text ||
      session.foundation_text ||
      session.world_summary ||
      session.story_summary ||
      ""
  );

  const lines = [
    `# ${title}`,
    "",
    `- Mode: ${mode === "novel" ? "Novel" : "Adventure"}`,
    `- Session ID: ${session.session_id || "Unknown"}`,
    `- Created: ${formatSessionDate(session.created_at)}`,
    `- Updated: ${formatSessionDate(session.updated_at)}`,
    `- Target words: ${session.target_words || "Default"}`,
    "",
    ...buildSurvivalMarkdown(session),
    "## World Profile",
    "",
    foundation || "No world profile is available.",
    "",
    "## Story",
    "",
  ];

  const storyMessages = messages.filter(
    (message) => message.role !== "system" && message.content
  );

  if (!storyMessages.length) {
    lines.push("No story messages are available yet.");
  }

  storyMessages.forEach((message, index) => {
    const label = message.role === "user" ? "You" : "AI";
    lines.push(`### ${index + 1}. ${label}`);
    lines.push("");
    lines.push(normalizeMarkdownText(message.content));

    if (Array.isArray(message.choices) && message.choices.length) {
      lines.push("");
      lines.push("Choices:");
      message.choices.forEach((choice) => {
        lines.push(`- ${normalizeMarkdownText(choice)}`);
      });
    }

    lines.push("");
  });

  return `${lines.join("\n").trim()}\n`;
}

function downloadTextFile(filename, content, mimeType = "text/markdown;charset=utf-8") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 0);
}

async function exportHistorySession(targetSessionId, triggerButton = null) {
  if (!targetSessionId) return;

  const originalText = triggerButton?.textContent || "";

  if (triggerButton) {
    triggerButton.disabled = true;
    triggerButton.textContent = "Exporting...";
  }

  try {
    const data = await requestJson(
      `${API_BASE}/game/${encodeURIComponent(targetSessionId)}`
    );
    const title = data?.session?.title || "Untitled Story";
    const markdown = buildHistoryMarkdown(data);

    downloadTextFile(`${sanitizeFilename(title)}.md`, markdown);
  } catch (err) {
    console.error(err);
    alert(err.message || String(err));
  } finally {
    if (triggerButton) {
      triggerButton.disabled = false;
      triggerButton.textContent = originalText;
    }
  }
}

function renderSavePreviewEmpty() {
  if (!savePreviewPanel) return;

  savePreviewPanel.removeAttribute("aria-busy");
  savePreviewPanel.innerHTML = `
    <div class="save-preview-empty">
      <p class="eyebrow">Archive Preview</p>
      <h2>Select a story</h2>
      <p>
        Preview a story from History to review its world profile, recent scenes,
        and available choices before continuing.
      </p>
    </div>
  `;
}

async function previewSession(targetSessionId) {
  if (!targetSessionId || !savePreviewPanel) return;

  activePreviewSessionId = targetSessionId;
  renderSavedSessions();

  savePreviewPanel.setAttribute("aria-busy", "true");
  savePreviewPanel.innerHTML = `
    <div class="save-preview-loading">
      <p class="eyebrow">Opening Archive</p>
      <h2>Loading preview...</h2>
      <p>Fetching this story from the backend.</p>
    </div>
  `;

  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  savePreviewPanel.scrollIntoView({
    behavior: reduceMotion ? "auto" : "smooth",
    block: "nearest",
  });

  try {
    let data = savePreviewCache.get(targetSessionId);

    if (!data) {
      data = await requestJson(
        `${API_BASE}/game/${encodeURIComponent(targetSessionId)}`
      );
      savePreviewCache.set(targetSessionId, data);
    }

    if (activePreviewSessionId !== targetSessionId) return;

    renderSavePreview(data);
    pulsePortal(0.45);
  } catch (err) {
    if (activePreviewSessionId !== targetSessionId) return;

    savePreviewPanel.removeAttribute("aria-busy");
    savePreviewPanel.innerHTML = `
      <div class="save-preview-empty error-state">
        <p class="eyebrow">Preview Error</p>
        <h2>Could not open this story</h2>
        <p>${escapeHtml(err.message || String(err))}</p>
      </div>
    `;
  }
}

function renderSavePreview(data) {
  if (!savePreviewPanel) return;

  const session = data?.session || {};
  const messages = Array.isArray(data?.messages) ? data.messages : [];
  const mode = getSessionMode(session);
  const modeLabel = mode === "novel" ? "Novel" : "Adventure";
  const title = session.title || "Untitled Story";
  const foundation =
    data?.foundation_text ||
    session.foundation_text ||
    session.world_summary ||
    session.story_summary ||
    "";
  const recentMessages = messages
    .filter((message) => message.role !== "system" && message.content)
    .slice(-4);
  const lastChoices =
    [...messages]
      .reverse()
      .find((message) => message.role === "ai" && message.choices?.length)
      ?.choices || [];

  savePreviewPanel.removeAttribute("aria-busy");
  savePreviewPanel.innerHTML = `
    <div class="save-preview-header">
      <div>
        <p class="eyebrow">Archive Preview</p>
        <h2>${escapeHtml(title)}</h2>
      </div>
      <button type="button" class="ghost small-btn preview-close-btn">
        Close
      </button>
    </div>

    <div class="save-preview-meta">
      <span class="save-mode ${mode}">${modeLabel}</span>
      <span>${escapeHtml(formatSessionDate(session.updated_at))}</span>
      <span>${escapeHtml(session.target_words || "Default")} words/turn</span>
    </div>

    ${mode === "adventure" ? renderSurvivalPreviewHtml(session) : ""}

    <section class="save-preview-section">
      <h3>World Profile</h3>
      ${
        foundation
          ? `<p>${escapeHtml(truncateText(foundation, 900))}</p>`
          : `<p class="save-preview-muted">No world profile is available for this session yet.</p>`
      }
    </section>

    <section class="save-preview-section">
      <h3>Recent Scenes</h3>
      ${
        recentMessages.length
          ? recentMessages
              .map(
                (message) => `
                  <article class="save-preview-message ${message.role === "user" ? "user" : "ai"}">
                    <span>${message.role === "user" ? "You" : "AI"}</span>
                    <p>${escapeHtml(truncateText(message.content, 360))}</p>
                  </article>
                `
              )
              .join("")
          : `<p class="save-preview-muted">No recent story messages are available yet.</p>`
      }
    </section>

    <section class="save-preview-section">
      <h3>Latest Choices</h3>
      ${
        lastChoices.length
          ? `<ul class="save-preview-choices">
              ${lastChoices
                .map((choice) => `<li>${escapeHtml(choice)}</li>`)
                .join("")}
            </ul>`
          : `<p class="save-preview-muted">No choices are available on the latest AI message.</p>`
      }
    </section>

    <div class="save-preview-actions">
      <button type="button" class="ghost preview-rename-btn">
        Rename
      </button>

      <button type="button" class="ghost preview-export-btn">
        Export .md
      </button>

      <button type="button" class="primary-btn preview-continue-btn">
        Continue This Story
      </button>
    </div>
  `;

  savePreviewPanel
    .querySelector(".preview-close-btn")
    ?.addEventListener("click", () => {
      closeSavePreview();
    });

  savePreviewPanel
    .querySelector(".preview-rename-btn")
    ?.addEventListener("click", () => {
      renameHistorySession(session.session_id || activePreviewSessionId, title);
    });

  savePreviewPanel
    .querySelector(".preview-export-btn")
    ?.addEventListener("click", (event) => {
      exportHistorySession(session.session_id || activePreviewSessionId, event.currentTarget);
    });

  savePreviewPanel
    .querySelector(".preview-continue-btn")
    ?.addEventListener("click", () => {
      continueSession(session.session_id || activePreviewSessionId);
    });
}

function closeSavePreview(options = {}) {
  activePreviewSessionId = "";
  renderSavePreviewEmpty();

  if (options.render !== false) {
    renderSavedSessions();
  }
}

function renderFoundationContent(text) {
  if (!foundationText) return;

  const safeText = (text || "").trim();

  if (!safeText) {
    foundationText.innerHTML = "<p>No world profile available.</p>";
    return;
  }

  const paragraphs = safeText
    .split(/\n\s*\n|\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  foundationText.innerHTML = paragraphs
    .map((p) => `<p>${escapeHtml(p)}</p>`)
    .join("");
}
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
async function continueSession(targetSessionId) {
  try {
    const data = await requestJson(`${API_BASE}/game/${encodeURIComponent(targetSessionId)}`);

    sessionId = targetSessionId;
    sessionStorage.setItem("session_id", sessionId);
    setCurrentSessionSaved(getSessionSavedFlag(data.session));
    setCurrentSessionTitle(data.session?.title || "");

    storyLog.innerHTML = "";
    choicesBox.innerHTML = "";

    sessionLabel.textContent = sessionId;

    applySessionMode(data.session?.mode || "adventure");
    if (currentSessionMode === "adventure") {
      syncAdventureQuestStateFromSession(data.session || {});
    } else {
      updateAdventureQuestHud();
    }

    if (turnTargetWords) {
      turnTargetWords.value =
        data.session?.target_words ||
        (currentSessionMode === "novel" ? 700 : 600);
    }

    renderFoundationContent(
      data.foundation_text || data.session?.foundation_text || ""
    );
    updateFoundationSidebar();

    showPage(gamePage);

    if (customAction) {
      customAction.value = "";
      customAction.focus();
    }

    const messages = data.messages || [];

    for (const msg of messages) {
      if (msg.role === "system") continue;

      await addMessage(
        msg.role === "user" ? "user" : "ai",
        msg.content
      );
    }

    const lastAiMessage = [...messages]
      .reverse()
      .find((m) => m.role === "ai" && m.choices?.length);

    if (lastAiMessage) {
      renderChoicesFromArray(lastAiMessage.choices);
    } else {
      choicesBox.innerHTML =
        "<p style='color:var(--subtle);padding:8px 4px;font-size:0.86rem'>This history item does not have saved choices yet.</p>";
    }

    pulseAmbient();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteHistorySession(targetSessionId) {
  const confirmed = await confirmDialog(
    "Delete this history item? Story data and memory will be removed."
  );
  if (!confirmed) return;
  try {
    await requestJson(`${API_BASE}/game/sessions/${encodeURIComponent(targetSessionId)}`, { method: "DELETE" });
    savePreviewCache.delete(targetSessionId);

    if (activePreviewSessionId === targetSessionId) {
      closeSavePreview({ render: false });
    }

    if (sessionId === targetSessionId) {
      clearCurrentSessionReference();
      applySessionMode("adventure");
      storyLog.innerHTML = "";
      choicesBox.innerHTML = "";
if (customAction) {
  customAction.value = "";
}
    }
    await loadSessions();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteSession(targetSessionId) {
  return deleteHistorySession(targetSessionId);
}

// ── Auth state ────────────────────────────────────────────────────────────────

onAuthStateChanged(auth, async (user) => {
  const checkId = ++authStatusCheckId;
  hideAuthLoading();

  if (loginGoogleBtn) {
    loginGoogleBtn.disabled = false;

    const span = loginGoogleBtn.querySelector("span");
    if (span) {
      span.textContent = "Tiếp tục với Google";
    }
  }

  if (!user && !isGuest) {
    updateUserUI(null);
    hideAccountStatusPanel();
    hideAiLoading();
    loadWorldCatalog({ force: true });
    return;
  }

  if (user) {
    if (user.isAnonymous) {
      isGuest = true;
    } else {
      isGuest = false;
      // Check email verification for Email/Password provider
      const isEmailProvider = user.providerData.some(p => p.providerId === 'password');
      if (isEmailProvider && !user.emailVerified) {
        updateUserUI(user);
        showPage(verifyEmailPage);
        setActiveNav(null);
        hideAiLoading();
        return;
      }
    }

    updateUserUI(user);

    try {
      const isAuthPageActive = loginPage.classList.contains("active") || 
                               registerPage.classList.contains("active") || 
                               verifyEmailPage.classList.contains("active");

      if (isAuthPageActive) {
        showAccountStatusPanel({
          tone: "info",
          eyebrow: "Checking",
          title: "Checking account access",
          message: "Verifying maintenance and account status before opening the story portal.",
        });
      }

      const status = await getAccountStatus();
      if (checkId !== authStatusCheckId) return;

      const isBlocked = renderAccountBlock(status);
      if (isBlocked) {
        showPage(loginPage);
        setActiveNav(null);
        hideAiLoading();
        return;
      }

      if (isAuthPageActive) {
        showPage(landingPage);
      }
      loadWorldCatalog({ force: true });
    } catch (err) {
      console.error(err);
      if (checkId !== authStatusCheckId) return;

      showAccountStatusPanel({
        tone: "error",
        eyebrow: "Connection",
        title: "Could not verify account status",
        message:
          err?.message ||
          "Start the backend API, then sign in again to continue.",
      });
      showPage(loginPage);
      setActiveNav(null);
      hideAiLoading();
    }
  }
});

// Initial state: show login until Firebase resolves
loadWorldCatalog();
showPage(loginPage);

loginEmailBtn?.addEventListener("click", async () => {
  clearAuthError(loginError);
  hideAccountStatusPanel();
  const email = loginEmail.value.trim();
  const password = loginPassword.value.trim();

  if (!email || !password) {
    showAuthError(loginError, "Vui lòng nhập email và mật khẩu.");
    return;
  }

  try {
    loginEmailBtn.disabled = true;
    loginEmailBtn.textContent = "Đang đăng nhập...";
    showAuthLoading();
    await Promise.all([
      signInWithEmailAndPassword(auth, email, password),
      sleep(2200),
    ]);
  } catch (err) {
    console.error(err);
    showAuthError(loginError, getFriendlyAuthError(err));
  } finally {
    loginEmailBtn.disabled = false;
    loginEmailBtn.textContent = "Login";
    hideAuthLoading();
  }
});

registerSubmitBtn?.addEventListener("click", async () => {
  clearAuthError(registerError);
  const email = registerEmail.value.trim();
  const password = registerPassword.value.trim();
  const confirmPassword = registerPasswordConfirm.value.trim();

  if (!email || !password) {
    showAuthError(registerError, "Vui lòng nhập email và mật khẩu.");
    return;
  }

  if (password !== confirmPassword) {
    showAuthError(registerError, "Mật khẩu nhập lại không khớp.");
    return;
  }

  if (password.length < 6) {
    showAuthError(registerError, "Mật khẩu phải ít nhất 6 ký tự.");
    return;
  }

  try {
    registerSubmitBtn.disabled = true;
    registerSubmitBtn.textContent = "Đang tạo tài khoản...";
    showAuthLoading();

    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    // Send verification email
    await sendEmailVerification(user);

    showAuthError(
      registerError,
      "Đăng ký thành công! Đang chuyển đến trang xác thực email..."
    );

    // Green success styles
    registerError.style.background = "rgba(80,255,120,0.12)";
    registerError.style.border = "1px solid rgba(80,255,120,0.25)";
    registerError.style.color = "#b8ffca";

    await sleep(2200);
    showPage(verifyEmailPage);
  } catch (err) {
    console.error(err);
    registerError.style.background = "";
    registerError.style.border = "";
    registerError.style.color = "";
    showAuthError(registerError, getFriendlyAuthError(err));
  } finally {
    registerSubmitBtn.disabled = false;
    registerSubmitBtn.textContent = "Register";
    hideAuthLoading();
  }
});

goToRegisterBtn?.addEventListener("click", () => {
  resetAuthPages();
  showPage(registerPage);
});

goToLoginBtn?.addEventListener("click", () => {
  resetAuthPages();
  showPage(loginPage);
});

// Forgot password buttons
const forgotPasswordBtn = document.getElementById("forgotPasswordBtn");
const backToLoginFromForgotBtn = document.getElementById("backToLoginFromForgotBtn");
const forgotSubmitBtn = document.getElementById("forgotSubmitBtn");

forgotPasswordBtn?.addEventListener("click", () => {
  resetAuthPages();
  showPage(forgotPasswordPage);
});

backToLoginFromForgotBtn?.addEventListener("click", () => {
  resetAuthPages();
  showPage(loginPage);
});

forgotSubmitBtn?.addEventListener("click", async () => {
  const forgotError = document.getElementById("forgotError");
  const email = document.getElementById("forgotEmail")?.value.trim();
  clearAuthError(forgotError);

  if (!email) {
    showAuthError(forgotError, "Vui lòng nhập địa chỉ email.");
    return;
  }

  try {
    forgotSubmitBtn.disabled = true;
    forgotSubmitBtn.textContent = "Đang gửi...";
    showAuthLoading();

    await sendPasswordResetEmail(auth, email);

    forgotError.style.background = "rgba(80,255,120,0.12)";
    forgotError.style.border = "1px solid rgba(80,255,120,0.25)";
    forgotError.style.color = "#b8ffca";
    showAuthError(forgotError, "Liên kết khôi phục mật khẩu đã được gửi đến email của bạn.");

    await sleep(3000);
    resetAuthPages();
    showPage(loginPage);
  } catch (err) {
    console.error(err);
    forgotError.style.background = "";
    forgotError.style.border = "";
    forgotError.style.color = "";
    let errMsg = "Có lỗi xảy ra. Hãy thử lại.";
    if (err?.code?.includes("user-not-found")) {
      errMsg = "Không tìm thấy người dùng với email này.";
    } else if (err?.code?.includes("invalid-email")) {
      errMsg = "Email không hợp lệ.";
    }
    showAuthError(forgotError, errMsg);
  } finally {
    forgotSubmitBtn.disabled = false;
    forgotSubmitBtn.textContent = "Gửi liên kết khôi phục";
    hideAuthLoading();
  }
});

// Verify email buttons
const resendVerifyEmailBtn = document.getElementById("resendVerifyEmailBtn");
const verifyEmailLogoutBtn = document.getElementById("verifyEmailLogoutBtn");

resendVerifyEmailBtn?.addEventListener("click", async () => {
  const user = auth.currentUser;
  if (!user) return;

  const verifyEmailError = document.getElementById("verifyEmailError");
  try {
    resendVerifyEmailBtn.disabled = true;
    resendVerifyEmailBtn.textContent = "Đang gửi...";

    await sendEmailVerification(user);

    verifyEmailError.style.background = "rgba(80,255,120,0.12)";
    verifyEmailError.style.border = "1px solid rgba(80,255,120,0.25)";
    verifyEmailError.style.color = "#b8ffca";
    showAuthError(verifyEmailError, "Đã gửi lại email xác thực thành công!");

    // Cooldown 60s
    let cooldown = 60;
    const cooldownInterval = setInterval(() => {
      cooldown--;
      if (cooldown <= 0) {
        clearInterval(cooldownInterval);
        resendVerifyEmailBtn.disabled = false;
        resendVerifyEmailBtn.textContent = "Gửi lại Email xác thực";
        clearAuthError(verifyEmailError);
      } else {
        resendVerifyEmailBtn.textContent = `Gửi lại sau (${cooldown}s)`;
      }
    }, 1000);
  } catch (err) {
    console.error(err);
    verifyEmailError.style.background = "";
    verifyEmailError.style.border = "";
    verifyEmailError.style.color = "";
    showAuthError(verifyEmailError, "Không thể gửi email xác thực. Thử lại sau.");
    resendVerifyEmailBtn.disabled = false;
    resendVerifyEmailBtn.textContent = "Gửi lại Email xác thực";
  }
});

verifyEmailLogoutBtn?.addEventListener("click", async () => {
  try {
    showAuthLoading();
    await signOut(auth);
    isGuest = false;
    resetAuthPages();
    showPage(loginPage);
  } catch (err) {
    console.error(err);
  } finally {
    hideAuthLoading();
  }
});

function togglePassword(input, button) {
  const isPassword = input.type === "password";
  input.type = isPassword ? "text" : "password";

  const eye = button.querySelector(".eye-icon");
  const eyeOff = button.querySelector(".eye-off-icon");
  if (eye && eyeOff) {
    if (isPassword) {
      eye.classList.remove("hidden");
      eyeOff.classList.add("hidden");
    } else {
      eye.classList.add("hidden");
      eyeOff.classList.remove("hidden");
    }
  }
}

toggleLoginPassword?.addEventListener("click", () => {
  togglePassword(loginPassword, toggleLoginPassword);
});

toggleRegisterPassword?.addEventListener("click", () => {
  togglePassword(registerPassword, toggleRegisterPassword);
});

toggleRegisterPasswordConfirm?.addEventListener("click", () => {
  togglePassword(
    registerPasswordConfirm,
    toggleRegisterPasswordConfirm
  );
});
function showAuthLoading() {

  randomizeLoadingText();

  authLoadingOverlay?.classList.remove("hidden");

  clearInterval(loadingLoreInterval);

  loadingLoreInterval = setInterval(() => {
    randomizeLoadingText();
  }, 2200);
}

function hideAuthLoading() {

  clearInterval(loadingLoreInterval);

  authLoadingOverlay?.classList.add("hidden");
}
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function showAuthError(target, message) {
  if (!target) return;

  target.textContent = message;
  target.classList.remove("hidden");
}

function clearAuthError(target) {
  if (!target) return;

  target.textContent = "";
  target.classList.add("hidden");
}

function getFriendlyAuthError(err) {
  const code = err?.code || "";

  if (code.includes("auth/invalid-credential")) {
    return "Email hoặc mật khẩu không đúng, hoặc tài khoản chưa tồn tại.";
  }

  if (code.includes("auth/user-not-found")) {
    return "Tài khoản này chưa tồn tại. Hãy đăng ký trước.";
  }

  if (code.includes("auth/wrong-password")) {
    return "Mật khẩu không đúng.";
  }

  if (code.includes("auth/email-already-in-use")) {
    return "Email này đã được đăng ký. Hãy đăng nhập.";
  }

  if (code.includes("auth/weak-password")) {
    return "Mật khẩu quá yếu. Hãy dùng ít nhất 6 ký tự.";
  }

  if (code.includes("auth/invalid-email")) {
    return "Email không hợp lệ.";
  }

  return "Có lỗi xảy ra. Vui lòng thử lại.";
}


function resetAuthPages() {
  // LOGIN
  if (loginEmail) loginEmail.value = "";
  if (loginPassword) loginPassword.value = "";
  clearAuthError(loginError);

  // REGISTER
  if (registerEmail) registerEmail.value = "";
  if (registerPassword) registerPassword.value = "";
  if (registerPasswordConfirm) {
    registerPasswordConfirm.value = "";
  }
  clearAuthError(registerError);

  // FORGOT PASSWORD
  const forgotEmail = document.getElementById("forgotEmail");
  const forgotError = document.getElementById("forgotError");
  if (forgotEmail) forgotEmail.value = "";
  if (forgotError) clearAuthError(forgotError);

  // VERIFY EMAIL
  const verifyEmailError = document.getElementById("verifyEmailError");
  if (verifyEmailError) clearAuthError(verifyEmailError);

  // reset password visibility types
  if (loginPassword) loginPassword.type = "password";
  if (registerPassword) registerPassword.type = "password";
  if (registerPasswordConfirm) {
    registerPasswordConfirm.type = "password";
  }

  // reset password visibility icons
  document.querySelectorAll(".password-toggle").forEach(button => {
    const eye = button.querySelector(".eye-icon");
    const eyeOff = button.querySelector(".eye-off-icon");
    if (eye && eyeOff) {
      eye.classList.remove("hidden");
      eyeOff.classList.add("hidden");
    }
  });
}

const authLoadingText =
  document.getElementById("authLoadingText");

const loadingLoreTexts = [
  "Connecting to the world of AI Story Adventure...",
  "Forging a new destiny...",
  "Summoning forgotten memories...",
  "Awakening ancient kingdoms...",
  "The AI is weaving your legend...",
  "Shaping a world beyond imagination...",
  "Opening the gates of adventure...",
  "The story is beginning to unfold...",
  "Factions are rising across the realm...",
  "A new fate is being written..."
];

function randomizeLoadingText() {
  if (!authLoadingText) return;

  const randomText =
    loadingLoreTexts[
      Math.floor(Math.random() * loadingLoreTexts.length)
    ];

  authLoadingText.style.opacity = 0;

  setTimeout(() => {
    authLoadingText.textContent = randomText;
    authLoadingText.style.opacity = 1;
  }, 180);
}

const worldLoadingText =
  document.getElementById("worldLoadingText");

const worldLoreTexts = [
  "The AI is weaving together lands, memories, and the fate that awaits you...",
  "Ancient kingdoms are rising from forgotten ashes...",
  "Lost civilizations are being reconstructed...",
  "Factions across the realm are awakening...",
  "Your destiny is taking shape...",
  "The world is remembering its ancient history...",
  "A new legend is about to begin...",
  "Mysteries are forming beyond the horizon...",
  "The threads of fate are intertwining...",
  "The realm is being forged around your choices..."
];

function randomizeWorldLoadingText() {
  if (!worldLoadingText) return;
  if (loadingState.context === "firebase-clock") return;

  const randomText =
    worldLoreTexts[
      Math.floor(Math.random() * worldLoreTexts.length)
    ];

  worldLoadingText.style.opacity = 0;

  setTimeout(() => {
    worldLoadingText.textContent = randomText;
    worldLoadingText.style.opacity = 1;
  }, 180);
}

homeNavBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(landingPage);
    setActiveNav(homeTabBtn);
  });
});

homeTabBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(landingPage);
    setActiveNav(homeTabBtn);
  });
});

discoverTabBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(discoverPage);
    setActiveNav(discoverTabBtn);
    await loadWorldCatalog();
  });
});

savesTabBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(continuePage);
    setActiveNav(savesTabBtn);
    await loadSessions();
  });
});

aboutBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(aboutPage);
    setActiveNav(null);
    revealAboutSections();
  });
});

async function openTrustPage() {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    closeAvatarDropdown();
    showPage(trustPage);
    setActiveNav(null);
    window.scrollTo({ top: 0, behavior: reducedMotionMedia.matches ? "auto" : "smooth" });
  });
}

createBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    openCreateModal();
  });
});

globalSearchToggle?.addEventListener("click", (event) => {
  event.stopPropagation();
  toggleGlobalSearch();
});

globalSearchInput?.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeGlobalSearch();
    globalSearchToggle?.focus();
  }
});

mobileHomeBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(landingPage);
    setActiveNav(mobileHomeBtn);
  });
});

mobileDiscoverBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(discoverPage);
    setActiveNav(mobileDiscoverBtn);
    await loadWorldCatalog();
  });
});

mobileHistoryBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    showPage(continuePage);
    setActiveNav(mobileHistoryBtn);
    await loadSessions();
  });
});

mobileCreateBtn?.addEventListener("click", async () => {
  await guardUnsavedDraftNavigation(async () => {
    closeGlobalSearch();
    setActiveNav(mobileCreateBtn);
    openCreateModal();
  });
});

navAvatarBtn?.addEventListener("click", (event) => {
  event.stopPropagation();

  if (!auth.currentUser && !isGuest) {
    showPage(loginPage);
    setActiveNav(null);
    return;
  }

  toggleAvatarDropdown();
});

function openProfileSettingsPage(event) {
  event?.preventDefault?.();
  event?.stopPropagation?.();

  closeAvatarDropdown();

  if (!profilePage) {
    console.error("Profile Settings page is missing from the DOM.");
    return;
  }

  showPage(profilePage);
  setActiveNav(null);
}

dropdownProfileBtn?.addEventListener("click", openProfileSettingsPage);

document.addEventListener(
  "click",
  (event) => {
    const profileButton = event.target?.closest?.("#dropdownProfileBtn");

    if (!profileButton) return;

    openProfileSettingsPage(event);
  },
  true
);

dropdownLogoutBtn?.addEventListener("click", async () => {
  closeAvatarDropdown();
  await handleLogoutRequest();
});

document.addEventListener("click", (event) => {
  if (!avatarDropdown || avatarDropdown.classList.contains("hidden")) {
    if (
      document.body.classList.contains("mobile-search-open") &&
      !event.target?.closest?.(".nav-search") &&
      !event.target?.closest?.("#globalSearchToggle")
    ) {
      closeGlobalSearch();
    }
    return;
  }

  const menu = document.querySelector(".nav-user-menu");

  if (menu && !menu.contains(event.target)) {
    closeAvatarDropdown();
  }

  if (
    document.body.classList.contains("mobile-search-open") &&
    !event.target?.closest?.(".nav-search") &&
    !event.target?.closest?.("#globalSearchToggle")
  ) {
    closeGlobalSearch();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeCreateModal();
    closeAvatarDropdown();
    closeGlobalSearch();
  }
});

function normalizeCatalogWorld(world = {}) {
  return {
    id: world.id || "",
    title: world.title || "Untitled World",
    mode: world.mode || "Adventure",
    description: world.description || "",
    image: world.image || "linear-gradient(135deg, #101820, #34251c)",
    worldSeed: world.worldSeed || world.world_seed || "",
    longDescription:
      world.longDescription ||
      world.long_description ||
      world.worldSeed ||
      world.world_seed ||
      "",
    tags: Array.isArray(world.tags) ? world.tags : [],
  };
}

function setDiscoverStatus(message = "", type = "muted") {
  if (!discoverStatus) return;

  discoverStatus.textContent = message;
  discoverStatus.dataset.type = type;
  discoverStatus.classList.toggle("hidden", !message);
}

function updateDiscoverStats() {
  const adventureCount = communityWorlds.filter(
    (world) => String(world.mode).toLowerCase() === "adventure"
  ).length;
  const novelCount = communityWorlds.filter(
    (world) => String(world.mode).toLowerCase() === "novel"
  ).length;

  if (discoverTotalCount) discoverTotalCount.textContent = String(communityWorlds.length);
  if (discoverAdventureCount) discoverAdventureCount.textContent = String(adventureCount);
  if (discoverNovelCount) discoverNovelCount.textContent = String(novelCount);
}

function getFilteredCatalogWorlds() {
  const query = discoverSearchInput?.value.trim().toLowerCase() || "";
  const mode = discoverModeFilter?.value || "all";

  return communityWorlds.filter((world) => {
    const normalizedMode = String(world.mode || "").toLowerCase();
    const haystack = [
      world.title,
      world.description,
      world.worldSeed,
      world.longDescription,
      ...(world.tags || []),
    ]
      .join(" ")
      .toLowerCase();

    const matchesMode = mode === "all" || normalizedMode === mode;
    const matchesSearch = !query || haystack.includes(query);

    return matchesMode && matchesSearch;
  });
}

function renderDiscoverWorlds() {
  if (!discoverWorldGrid) return;

  updateDiscoverStats();
  discoverWorldGrid.innerHTML = "";

  const worlds = getFilteredCatalogWorlds();

  discoverEmptyState?.classList.toggle(
    "hidden",
    worldCatalogLoading || Boolean(worldCatalogError) || worlds.length > 0
  );

  if (worldCatalogLoading) {
    setDiscoverStatus("Loading backend world catalog...", "muted");
    return;
  }

  if (worldCatalogError) {
    setDiscoverStatus(worldCatalogError, "error");
    return;
  }

  setDiscoverStatus(
    worlds.length
      ? `${worlds.length} curated world${worlds.length === 1 ? "" : "s"} ready.`
      : "",
    "muted"
  );

  worlds.forEach((world) => {
    discoverWorldGrid.appendChild(renderWorldCard(world, "discover"));
  });
}

async function loadWorldCatalog({ force = false } = {}) {
  if (worldCatalogLoading) return;
  if (worldCatalogLoaded && !force) {
    renderHomeWorlds();
    renderDiscoverWorlds();
    return;
  }

  worldCatalogLoading = true;
  worldCatalogError = "";
  renderDiscoverWorlds();

  try {
    const data = await requestJson(`${API_BASE}/game/worlds`, {
      skipAuth: true,
    });

    const worlds = Array.isArray(data)
      ? data.map(normalizeCatalogWorld).filter((world) => world.id)
      : [];

    communityWorlds.length = 0;
    if (auth.currentUser) {
      try {
        const communityData = await requestJson(`${API_BASE}/game/discover`);
        if (Array.isArray(communityData)) {
          const loadedCommunity = communityData.map(normalizeCommunityWorld).filter(w => w.id);
          communityWorlds.push(...loadedCommunity);
        }
      } catch (err) {
        console.warn("Could not load community worlds:", err);
      }
    }

    creatorWorlds.length = 0;
    creatorWorlds.push(...worlds);
    novelWorlds = creatorWorlds.filter(
      (world) => String(world.mode).toLowerCase() === "novel"
    );

    featuredWorldIndex = Math.min(featuredWorldIndex, Math.max(creatorWorlds.length - 1, 0));
    worldCatalogLoaded = true;
    worldCatalogError = "";
  } catch (err) {
    console.error(err);
    creatorWorlds.length = 0;
    novelWorlds = [];
    featuredWorldIndex = 0;
    worldCatalogLoaded = false;
    worldCatalogError =
      "Could not load the backend world catalog. Check that the API is running.";
  } finally {
    worldCatalogLoading = false;
    renderHomeWorlds();
    renderDiscoverWorlds();
  }
}

async function openCatalogWorld(worldId, fallbackWorld = null) {
  if (!worldId) return;

  try {
    setDiscoverStatus("Opening world profile...", "muted");

    const data = await requestJson(
      `${API_BASE}/game/worlds/${encodeURIComponent(worldId)}`,
      { skipAuth: true }
    );

    selectCreatorWorld(normalizeCatalogWorld(data));
  } catch (err) {
    console.error(err);
    setDiscoverStatus(err.message || "Could not open this world.", "error");

    if (fallbackWorld && worldCatalogLoaded) {
      selectCreatorWorld(fallbackWorld);
    }
  }
}

function renderWorldCard(world) {
  const card = document.createElement("article");
  card.className = "world-card";
  card.style.setProperty("--card-bg", world.image);

  const isCommunity = world.isCommunity === true;
  const isAuthor = isCommunity && auth.currentUser && world.authorUid === auth.currentUser.uid;
  const badgeClass = isCommunity ? "community-badge" : "official-badge";
  const badgeLabel = isCommunity ? "Community" : "Official";
  const authorLabel = isCommunity ? `By: ${escapeHtml(world.authorName)}` : "Backend Catalog";

  card.innerHTML = `
    <div class="world-card-content">
      <span class="world-card-mode">${escapeHtml(world.mode)}</span>
      <span class="world-card-source ${badgeClass}">${badgeLabel}</span>
      <h3>${escapeHtml(world.title)}</h3>
      <p>${escapeHtml(world.description)}</p>
      ${
        world.tags?.length
          ? `<div class="world-card-tags">${world.tags
              .slice(0, 3)
              .map((tag) => `<span>${escapeHtml(tag)}</span>`)
              .join("")}</div>`
          : ""
      }
      <div class="world-card-footer" style="display:flex; justify-content:space-between; align-items:center; width:100%;">
        <span>${authorLabel}</span>
        ${isCommunity ? `
          <div style="display:flex; gap:10px; align-items:center;">
            <button class="like-btn ghost" data-id="${world.id}" type="button">
              ❤️ <span class="like-count">${world.likes}</span>
            </button>
            ${world.sessionId ? `<button class="read-log-btn ghost" data-id="${world.id}" type="button">📖 Read</button>` : ""}
            ${isAuthor ? `<button class="delete-pub-btn ghost" data-id="${world.id}" type="button" style="color: #ff4d4d; border-color: rgba(255, 77, 77, 0.3);">🗑️</button>` : ""}
          </div>
        ` : '<span>Start →</span>'}
      </div>
    </div>
  `;

  card.addEventListener("click", (e) => {
    if (e.target.closest('button')) return;
    openCatalogWorld(world.id, world);
  });

  if (isCommunity) {
    card.querySelector('.like-btn')?.addEventListener('click', async (e) => {
      e.stopPropagation();
      await likeCommunityWorld(world.id, card.querySelector('.like-count'));
    });
    if (world.sessionId) {
      card.querySelector('.read-log-btn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        openStoryReaderModal(world);
      });
    }
    card.querySelector('.delete-pub-btn')?.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (confirm("Bạn có chắc chắn muốn xóa bài xuất bản này? Hành động này không thể hoàn tác.")) {
        await deleteCommunityWorld(world.id);
      }
    });
  }

  return card;
}

function renderHomeWorlds() {
  if (originalsGrid) {
    originalsGrid.innerHTML = "";

    creatorWorlds.forEach((world) => {
      originalsGrid.appendChild(renderWorldCard(world));
    });
  }

  if (novelWorldsGrid) {
    novelWorldsGrid.innerHTML = "";

    novelWorlds.forEach((world) => {
      novelWorldsGrid.appendChild(renderWorldCard(world));
    });
  }

  renderFeaturedWorld();
}

function renderFeaturedWorld() {
  const world = creatorWorlds[featuredWorldIndex];

  if (!world) {
    if (featuredTitle) {
      featuredTitle.textContent = worldCatalogLoading
        ? "Loading worlds..."
        : "World catalog unavailable";
    }

    if (featuredDescription) {
      featuredDescription.textContent = worldCatalogLoading
        ? "Connecting to the backend catalog."
        : "Start the backend API to browse curated worlds.";
    }

    return;
  }

  if (featuredTitle) {
    featuredTitle.textContent = world.title;
  }

  if (featuredDescription) {
    featuredDescription.textContent = world.description;
  }

  const hero = document.querySelector(".home-hero");
  if (hero) {
    hero.style.setProperty("--featured-bg", world.image);
  }

  const dots = document.querySelectorAll(".hero-dots span");

  dots.forEach((dot, index) => {
    dot.classList.toggle(
      "active",
      index === featuredWorldIndex
    );
  });
}
function selectCreatorWorld(world) {
  selectedPresetWorld = world;

  if (!presetDetailPage) {
    console.error("Missing #presetDetailPage in index.html");
    alert("Missing preset detail page in HTML.");
    return;
  }

  renderPresetDetail(world);
  showPage(presetDetailPage);
  setActiveNav(null);
}

function renderPresetDetail(world) {
  if (!world) return;

  if (presetDetailHero) {
    presetDetailHero.style.setProperty(
      "--preset-detail-bg",
      world.image
    );
  }

  if (presetDetailMode) {
    presetDetailMode.textContent = world.mode || "Story";
    presetDetailMode.className =
      `preset-detail-mode ${(world.mode || "").toLowerCase()}`;
  }

  if (presetDetailTitle) {
    presetDetailTitle.textContent = world.title || "Untitled World";
  }

  if (presetDetailDescription) {
    presetDetailDescription.textContent =
      world.description || "";
  }

  if (presetDetailLore) {
    presetDetailLore.textContent =
      world.longDescription || world.worldSeed || "";
  }

  if (presetDetailTags) {
    presetDetailTags.innerHTML = "";

    const tags = world.tags || [];

    tags.forEach((tag) => {
      const chip = document.createElement("span");
      chip.textContent = tag;
      presetDetailTags.appendChild(chip);
    });
  }
}

startPresetWorldBtn?.addEventListener("click", () => {
  if (!selectedPresetWorld) return;

  if (selectedPresetWorld.mode === "Novel") {
    startNovelFromPreset(selectedPresetWorld);
    return;
  }

  if (selectedPresetWorld.mode === "Adventure") {
    startAdventureFromPreset(selectedPresetWorld);
    return;
  }
});
backToHomeFromPreset?.addEventListener("click", () => {
  showPage(landingPage);
  setActiveNav(homeTabBtn);
});
previewPresetSeedBtn?.addEventListener("click", () => {
  document
    .querySelector(".preset-lore-section")
    ?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
});

async function startNovelFromPreset(world) {
  if (!auth.currentUser && !isGuest) {
    showPage(loginPage);
    setActiveNav(null);
    return;
  }

  if (novelWorldSeed) {
  novelWorldSeed.value = world.worldSeed || "";
}

if (novelInitialTargetWords && !novelInitialTargetWords.value) {
  novelInitialTargetWords.value = 700;
}

await createNovelWorld({
  title: world.title,
  worldSeed: world.worldSeed || "",
  targetWords: getNumberValue(novelInitialTargetWords, 700),
});
}

async function createNovelWorld({
  title = "Untitled Novel",
  worldSeed = "",
  targetWords = 700,
} = {}) {
  try {
    setLoading(true, "novel-world");

    const data = await requestJsonWithRetry(
      `${API_BASE}/game/novel/world`,
      {
        method: "POST",
        body: JSON.stringify({
          title,
          world_seed: worldSeed,
          target_words: targetWords,
        }),
      },
      { context: "novel-world" }
    );

    novelSessionId = data.session_id;
    sessionId = data.session_id;

    sessionStorage.setItem("session_id", sessionId);
    setCurrentSessionSaved(getSessionSavedFlag(data.session));
    setCurrentSessionTitle(data.session?.title || "");

    novelWorldDraft = data.world_draft || "";
    novelQuestions = (data.questions || []).map((question, index) => ({
      ...question,
      question_id:
        question.question_id ||
        question.id ||
        `q${index + 1}`,
    }));
    novelAnswers = [];
    currentNovelQuestionIndex = 0;

    sessionLabel.textContent = sessionId;

    renderNovelQuestion();
    showPage(novelQuestionPage);
    setActiveNav(null);

  } catch (err) {
    console.error(err);
    if (!isRetryCancelledError(err)) {
      alert(err.message);
    }
  } finally {
    setLoading(false);
  }
}

createNovelWorldBtn?.addEventListener("click", async () => {
  if (!auth.currentUser && !isGuest) {
    showPage(loginPage);
    return;
  }

  if (isRequesting) return;

  await createNovelWorld({
    title: selectedPresetWorld?.title || "Untitled Novel",
    worldSeed: novelWorldSeed?.value.trim() || "",
    targetWords: getNumberValue(novelInitialTargetWords, 700),
  });
});

skipNovelWorldBtn?.addEventListener("click", async () => {
  if (!auth.currentUser && !isGuest) {
    showPage(loginPage);
    return;
  }

  if (isRequesting) return;

  if (novelWorldSeed) {
    novelWorldSeed.value = "";
  }

  await createNovelWorld({
    title: "Untitled Novel",
    worldSeed: "",
    targetWords: getNumberValue(novelInitialTargetWords, 700),
  });
});


function saveCurrentNovelAnswer() {
  const question = novelQuestions[currentNovelQuestionIndex];

  if (!question) return true;

  const answer = novelQuestionAnswer?.value.trim() || "";

  if (!answer) {
    alert("Please answer this question before continuing.");
    return false;
  }

  novelAnswers[currentNovelQuestionIndex] = {
    question_id:
      question.question_id ||
      question.id ||
      `q${currentNovelQuestionIndex + 1}`,
    question: question.question || question.text || "",
    answer,
  };

  return true;
}

novelQuestionNextBtn?.addEventListener("click", () => {
  if (!novelQuestions.length) return;

  novelAnswers[currentNovelQuestionIndex] = {
    question: novelQuestions[currentNovelQuestionIndex]?.question || "",
    answer: novelQuestionAnswer?.value.trim() || "",
  };

  if (currentNovelQuestionIndex < novelQuestions.length - 1) {
    currentNovelQuestionIndex += 1;
    renderNovelQuestion();
    return;
  }

  showPage(novelCharacterPage);
});

function startAdventureFromPreset(world) {
  if (!auth.currentUser && !isGuest) {
    showPage(loginPage);
    setActiveNav(null);
    return;
  }

  if (storyStyleInput) {
    storyStyleInput.value = world.worldSeed || "";
  }

  applySessionMode("adventure");
  openAdventureSetup();
}
heroNextBtn?.addEventListener("click", async () => {
  if (!creatorWorlds.length) {
    await loadWorldCatalog({ force: true });
    return;
  }

  featuredWorldIndex =
    (featuredWorldIndex + 1) % creatorWorlds.length;

  renderFeaturedWorld();
});

featuredStartBtn?.addEventListener("click", async () => {
  if (!creatorWorlds.length) {
    await loadWorldCatalog({ force: true });
    return;
  }

  const world = creatorWorlds[featuredWorldIndex];

  if (world) {
    await openCatalogWorld(world.id, world);
  }
});

closeCreateModalBtn?.addEventListener("click", () => {
  closeCreateModal();
});

createModeModal
  ?.querySelector(".create-modal-backdrop")
  ?.addEventListener("click", () => {
    closeCreateModal();
  });

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeCreateModal();
  }
});
document.addEventListener("click", (event) => {
  const chip = event.target.closest(".suggestion-chip");

  if (!chip) return;

  const targetId = chip.dataset.target;
  const target = document.getElementById(targetId);

  if (!target) return;

  target.value = chip.textContent.trim();
  target.focus();

  updateAdventureSummary();
  updateAdventurePreview();
});
createAdventureBtn?.addEventListener("click", () => {
  closeCreateModal();
  openAdventureSetup();
});
createNovelBtn?.addEventListener("click", () => {
  closeCreateModal();

  showPage(novelWorldPage);
  setActiveNav(null);
});

function openCreateModal() {
  createModeModal?.classList.remove("hidden");

  requestAnimationFrame(() => {
    createModeModal?.classList.add("visible");
  });
}

function closeCreateModal() {
  createModeModal?.classList.remove("visible");
  syncActiveNavToCurrentPage();

  setTimeout(() => {
    createModeModal?.classList.add("hidden");
  }, 180);
}

discoverSearchInput?.addEventListener("input", () => {
  renderDiscoverWorlds();
});

discoverModeFilter?.addEventListener("change", () => {
  renderDiscoverWorlds();
});

discoverRefreshBtn?.addEventListener("click", async () => {
  await loadWorldCatalog({ force: true });
});

saveSearchInput?.addEventListener("input", () => {
  renderSavedSessions();
});

saveModeFilter?.addEventListener("change", () => {
  renderSavedSessions();
});

saveSortSelect?.addEventListener("change", () => {
  renderSavedSessions();
});

clearSavesSearchBtn?.addEventListener("click", () => {
  if (saveSearchInput) {
    saveSearchInput.value = "";
    saveSearchInput.focus();
  }

  renderSavedSessions();
});

refreshSavesBtn?.addEventListener("click", async () => {
  await loadSessions();
});

aboutCreateBtn?.addEventListener("click", () => {
  openCreateModal();
});

aboutFinalCreateBtn?.addEventListener("click", () => {
  openCreateModal();
});

aboutHomeBtn?.addEventListener("click", () => {
  showPage(landingPage);
  setActiveNav(homeTabBtn);
});

openTrustFromLogin?.addEventListener("click", openTrustPage);

trustBackToLoginBtn?.addEventListener("click", () => {
  showPage(loginPage);
  setActiveNav(null);
  window.scrollTo({ top: 0, behavior: reducedMotionMedia.matches ? "auto" : "smooth" });
});

trustHomeBtn?.addEventListener("click", () => {
  const targetPage = auth.currentUser || isGuest ? landingPage : loginPage;
  showPage(targetPage);
  setActiveNav(targetPage === landingPage ? homeTabBtn : null);
  window.scrollTo({ top: 0, behavior: reducedMotionMedia.matches ? "auto" : "smooth" });
});

function revealAboutSections() {
  const sections = document.querySelectorAll(".about-reveal");

  if (
    aboutPage?.classList.contains("active") &&
    getMotionApi() &&
    !reducedMotionMedia.matches
  ) {
    queueImmersiveMotionRefresh(aboutPage);
    return;
  }

  sections.forEach((section, index) => {
    section.classList.remove("visible");

    setTimeout(() => {
      section.classList.add("visible");
    }, index * 120);
  });
}

function openAvatarDropdown() {
  if (avatarCloseTimer) {
    clearTimeout(avatarCloseTimer);
    avatarCloseTimer = null;
  }

  avatarDropdown?.classList.remove("hidden");
  navAvatarBtn?.setAttribute("aria-expanded", "true");

  requestAnimationFrame(() => {
    avatarDropdown?.classList.add("visible");
  });
}

function closeAvatarDropdown() {
  avatarDropdown?.classList.remove("visible");
  navAvatarBtn?.setAttribute("aria-expanded", "false");

  if (avatarCloseTimer) {
    clearTimeout(avatarCloseTimer);
  }

  avatarCloseTimer = setTimeout(() => {
    avatarDropdown?.classList.add("hidden");
    avatarCloseTimer = null;
  }, 160);
}

function toggleAvatarDropdown() {
  if (!avatarDropdown) return;

  if (avatarDropdown.classList.contains("hidden")) {
    openAvatarDropdown();
  } else {
    closeAvatarDropdown();
  }
}

function renderAdventureStep() {
  const steps = document.querySelectorAll(".adventure-step");
  const dots = document.querySelectorAll(
    "#setupPage .adventure-dossier-progress span"
  );
  adventureProgressItems.forEach((item) => {
  item.classList.toggle(
    "active",
    Number(item.dataset.progress) === currentAdventureStep
  );
});

updateAdventurePreview();
  steps.forEach((step, index) => {
    step.classList.toggle("active", index === currentAdventureStep);
  });

  dots.forEach((dot, index) => {
    dot.classList.toggle("active", index === currentAdventureStep);
  });

  if (adventureStepLabel) {
    adventureStepLabel.textContent =
      `Step ${currentAdventureStep + 1} of ${totalAdventureSteps}`;
  }

  if (adventurePrevBtn) {
    adventurePrevBtn.style.visibility =
      currentAdventureStep === 0 ? "hidden" : "visible";
  }

  if (adventureNextBtn) {
    adventureNextBtn.textContent =
      currentAdventureStep === totalAdventureSteps - 1
        ? "Start Adventure"
        : "Next";
  }

  updateAdventureSummary();
}

function updateAdventureSummary() {
  const questState = syncAdventureQuestStateFromInputs();

  if (summaryPlayerName) {
    summaryPlayerName.textContent =
      questState.playerName || "Unknown";
  }

  if (summaryGender) {
    summaryGender.textContent =
      questState.startingCondition || "AI decides";
  }

  if (summaryPersonality) {
    summaryPersonality.textContent =
      questState.role || "Wanderer";
  }

  if (summaryStoryStyle) {
    summaryStoryStyle.textContent =
      questState.region || "AI creates";
  }

  if (summaryAdventureOrigin) {
    summaryAdventureOrigin.textContent =
      questState.objective || "Survive and move forward";
  }

  if (summaryAdventureGoal) {
    summaryAdventureGoal.textContent =
      questState.threat || "AI creates";
  }

  if (summaryAdventureRisk) {
    summaryAdventureRisk.textContent =
      questState.loadout || "Light supplies";
  }

  if (summaryAdventureSeed) {
    summaryAdventureSeed.textContent =
      questState.seed || "No style seed will be sent.";
  }
}

function validateAdventureStep() {
  if (currentAdventureStep === 0) {
    if (!playerNameInput?.value.trim()) {
      alert("Please enter your character name.");
      return false;
    }
  }

  return true;
}

adventureNextBtn?.addEventListener("click", async () => {
  const ok = validateAdventureStep();

  if (!ok) return;

  if (currentAdventureStep < totalAdventureSteps - 1) {
    currentAdventureStep += 1;
    renderAdventureStep();
    return;
  }

  await startAdventureGame();
});

adventurePrevBtn?.addEventListener("click", () => {
  if (currentAdventureStep <= 0) return;

  currentAdventureStep -= 1;
  renderAdventureStep();
});

function updateFoundationSidebar() {
  const isAdventure = currentSessionMode === "adventure";
  const questState = isAdventure ? adventureQuestState : null;
  const setMetaLabel = (node, label) => {
    if (node?.previousElementSibling) node.previousElementSibling.textContent = label;
  };

  if (isAdventure) {
    setMetaLabel(foundationCharacterGender, "Condition");
    setMetaLabel(foundationCharacterPersonality, "Role");
    setMetaLabel(foundationCharacterStyle, "Region");
    setMetaLabel(foundationAdventureOrigin, "Objective");
    setMetaLabel(foundationAdventureGoal, "Threat");
    setMetaLabel(foundationAdventureRisk, "Loadout");
    setMetaLabel(foundationAdventureSeed, "Last note");
  } else {
    setMetaLabel(foundationCharacterGender, "Gender");
    setMetaLabel(foundationCharacterPersonality, "Personality");
    setMetaLabel(foundationCharacterStyle, "Style");
  }

  if (foundationModeBadge) {
    foundationModeBadge.textContent =
      currentSessionMode === "novel" ? "Novel Mode" : "Survival Run";
  }

  if (foundationPlayerBadge) {
    foundationPlayerBadge.textContent =
      isAdventure
        ? questState?.playerName || "Unknown Hero"
        : novelPlayerName?.value.trim() || "Unknown Hero";
  }

  if (foundationToneBadge) {
    foundationToneBadge.textContent = "AI Generated";
  }

  if (foundationCharacterName) {
    foundationCharacterName.textContent =
      isAdventure
        ? questState?.playerName || "Unknown"
        : novelPlayerName?.value.trim() || "Unknown";
  }

  if (foundationCharacterGender) {
    foundationCharacterGender.textContent =
      isAdventure
        ? questState?.startingCondition || questState?.gender || "AI decides"
        : novelGender?.value.trim() || "AI decides";
  }

  if (foundationCharacterPersonality) {
    foundationCharacterPersonality.textContent =
      isAdventure
        ? questState?.role || questState?.personality || "AI generated"
        : novelPersonality?.value.trim() || "AI generated";
  }

  if (foundationCharacterStyle) {
    foundationCharacterStyle.textContent =
      isAdventure
        ? questState?.region || questState?.storyStyle || "AI generated"
        : novelOccupation?.value.trim() || "AI generated";
  }

  if (foundationAdventureOrigin) {
    foundationAdventureOrigin.textContent = isAdventure
      ? displayAdventureValue(questState?.objective || questState?.origin)
      : "Novel mode";
  }

  if (foundationAdventureGoal) {
    foundationAdventureGoal.textContent = isAdventure
      ? displayAdventureValue(questState?.threat || questState?.goal)
      : "Novel mode";
  }

  if (foundationAdventureRisk) {
    foundationAdventureRisk.textContent = isAdventure
      ? displayAdventureValue(questState?.loadout || questState?.risk)
      : "Novel mode";
  }

  if (foundationAdventureSeed) {
    foundationAdventureSeed.textContent = isAdventure
      ? displayAdventureValue(questState?.lastSurvivalNote, "Run just opened")
      : "Novel mode";
  }

  if (foundationSurvivalDanger) {
    foundationSurvivalDanger.textContent = isAdventure
      ? `${clampSurvivalStat(questState?.danger, 3)}/5`
      : "Novel mode";
  }

  if (foundationSurvivalSupplies) {
    foundationSurvivalSupplies.textContent = isAdventure
      ? `${clampSurvivalStat(questState?.supplies, 3)}/5`
      : "Novel mode";
  }

  if (foundationSurvivalWounds) {
    foundationSurvivalWounds.textContent = isAdventure
      ? `${clampSurvivalStat(questState?.wounds, 0)}/5`
      : "Novel mode";
  }

  if (foundationSurvivalTime) {
    foundationSurvivalTime.textContent = isAdventure
      ? `${clampSurvivalStat(questState?.timePressure, 3)}/5`
      : "Novel mode";
  }

  updateAdventureQuestHud();
}



function formatStoryParagraphs(text) {
  const safeText = String(text || "").trim();

  if (!safeText) return "<p></p>";

  return safeText
    .split(/\n\s*\n|\n/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => `<p>${escapeHtml(p)}</p>`)
    .join("");
}

function updateGameplayModeUI() {
  const isNovel = currentSessionMode === "novel";

  document.body.dataset.mode = currentSessionMode;

  if (customAction) {
    customAction.placeholder = isNovel
      ? "Write your own direction for the next scene..."
      : "What survival move do you make?";
  }

  const heading = document.querySelector(".choice-panel-heading h3");

  if (heading) {
    heading.textContent = isNovel
      ? "Choose where the story goes next"
      : "Choose your next survival move";
  }

  updateAdventureQuestHud();
}

loadReaderPrefs();
applyReaderPrefs();
resizeComposer();
updateScrollFade();

readerFocusToggle?.addEventListener("click", () => {
  updateReaderPrefs({ focus: !readerPrefs.focus });
});

readerFontDown?.addEventListener("click", () => {
  updateReaderPrefs({ fontScale: readerPrefs.fontScale - 1 });
});

readerFontUp?.addEventListener("click", () => {
  updateReaderPrefs({ fontScale: readerPrefs.fontScale + 1 });
});

readerLineDown?.addEventListener("click", () => {
  updateReaderPrefs({ lineScale: readerPrefs.lineScale - 1 });
});

readerLineUp?.addEventListener("click", () => {
  updateReaderPrefs({ lineScale: readerPrefs.lineScale + 1 });
});

scrollLatestBtn?.addEventListener("click", () => {
  scrollStoryToLatest();
});

profileEditNameBtn?.addEventListener("click", () => {
  if (!auth.currentUser) {
    setProfileNameError("Please sign in before editing your profile.");
    return;
  }

  setProfileNameEditing(true);
});

profileNameSaveBtn?.addEventListener("click", async () => {
  await saveProfileDisplayName();
});

profileNameCancelBtn?.addEventListener("click", () => {
  setProfileNameEditing(false);
});

profileNameInput?.addEventListener("input", () => {
  setProfileNameError("");
});

profileNameInput?.addEventListener("keydown", async (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    await saveProfileDisplayName();
  }

  if (event.key === "Escape") {
    setProfileNameEditing(false);
  }
});

submitBtn?.addEventListener("click", async () => {
  await submitAction();
});

customAction?.addEventListener("input", () => {
  setComposerStatus("");
  resizeComposer();
});

customAction?.addEventListener("keydown", async (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    await submitAction();
  }
});

document.addEventListener(
  "click",
  (event) => {
    const setupBackBtn = event.target.closest("#backToLandingFromSetup");

    if (!setupBackBtn) return;

    event.preventDefault();
    event.stopPropagation();

    currentAdventureStep = 0;

    if (typeof closeCreateModal === "function") {
      closeCreateModal();
    }

    showPage(landingPage);

    if (typeof setActiveNav === "function") {
      setActiveNav(homeTabBtn);
    }
  },
  true
);

function updateAdventurePreview() {
  const questState = syncAdventureQuestStateFromInputs();

  if (previewPlayerName) {
    previewPlayerName.textContent =
      questState.playerName || "Waiting...";
  }

  if (previewGender) {
    previewGender.textContent =
      questState.startingCondition || "AI decides";
  }

  if (previewPersonality) {
    previewPersonality.textContent =
      questState.role || "Not defined";
  }

  if (previewStoryStyle) {
    previewStoryStyle.textContent =
      questState.region || "Not defined";
  }

  if (previewAdventureOrigin) {
    previewAdventureOrigin.textContent =
      questState.objective || "Not defined";
  }

  if (previewAdventureGoal) {
    previewAdventureGoal.textContent =
      questState.threat || "Not defined";
  }

  if (previewAdventureRisk) {
    previewAdventureRisk.textContent =
      questState.loadout || "Not defined";
  }

  if (previewAdventureSeed) {
    previewAdventureSeed.textContent =
      `Danger ${questState.danger}/5 · Supplies ${questState.supplies}/5 · Wounds ${questState.wounds}/5 · Time ${questState.timePressure}/5`;
  }
}

[
  playerNameInput,
  genderInput,
  personalityInput,
  storyStyleInput,
  adventureOriginInput,
  adventureGoalInput,
  adventureRiskInput,
].forEach((input) => {
  input?.addEventListener("input", () => {
    updateAdventureSummary();
    updateAdventurePreview();
  });
});



// ── Login Animations (3D Tilt & Spotlight) ────────────────────────────────────
function initLoginAnimations() {
  const loginLayout = document.querySelector('.login-layout');
  const loginCard = document.querySelector('.login-card');
  const authCard = document.querySelector('.auth-card');
  
  if (loginLayout) {
    loginLayout.addEventListener('mousemove', (e) => {
      const rect = loginLayout.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      loginLayout.style.setProperty('--mouse-x', `${x}px`);
      loginLayout.style.setProperty('--mouse-y', `${y}px`);
    });
  }

  const applyTilt = (element) => {
    if (!element) return;
    element.addEventListener('mousemove', (e) => {
      const rect = element.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = ((y - centerY) / centerY) * -5;
      const rotateY = ((x - centerX) / centerX) * 5;
      
      element.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });
    
    element.addEventListener('mouseleave', () => {
      element.style.transform = `perspective(1200px) rotateX(0deg) rotateY(0deg)`;
      setTimeout(() => {
        element.style.transition = 'transform 0.1s ease-out';
      }, 100);
      element.style.transition = 'transform 0.5s ease-out';
    });
    
    element.addEventListener('mouseenter', () => {
      element.style.transition = 'transform 0.1s ease-out';
    });
  };

  applyTilt(loginCard);
  applyTilt(authCard);

  // ── Runic Text Scrambler ────────────────────────────────────────────────────
  const eyebrow = document.querySelector('.eyebrow');
  if (eyebrow) {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZΣΛΔΦΘΨΩΞ!@#$&*";
    const originalText = eyebrow.innerText;
    let iterations = 0;
    
    const interval = setInterval(() => {
      eyebrow.innerText = originalText.split("").map((char, index) => {
        if (index < iterations || char === " ") return originalText[index];
        return letters[Math.floor(Math.random() * letters.length)];
      }).join("");
      
      if (iterations >= originalText.length) clearInterval(interval);
      iterations += 1 / 4;
    }, 30);
  }

  // ── Magnetic Hover Buttons ──────────────────────────────────────────────────
  const magneticButtons = document.querySelectorAll('.google-btn, .auth-btn');
  magneticButtons.forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      // Di chuyển nút một quãng ngắn (20% khoảng cách từ tâm)
      btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = `translate(0px, 0px)`;
      setTimeout(() => {
        btn.style.transition = 'all 0.22s ease';
      }, 100);
      btn.style.transition = 'transform 0.5s ease';
    });
    btn.addEventListener('mouseenter', () => {
      btn.style.transition = 'none'; // Bỏ transition để di chuyển theo chuột mượt hơn
    });
  });

  // ── Ripple Click Effect ──────────────────────────────────────────────────────
  const rippleButtons = document.querySelectorAll('.google-btn, .primary-btn');
  rippleButtons.forEach(btn => {
    btn.classList.add('ripple-container');
    btn.addEventListener('click', function (e) {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const ripple = document.createElement('span');
      ripple.classList.add('ripple');
      
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${x - size / 2}px`;
      ripple.style.top = `${y - size / 2}px`;
      
      this.appendChild(ripple);
      
      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
}

// Call init when script loads
initLoginAnimations();

/* =========================================================================
   ABOUT PAGE UPGRADE: DYNAMIC INTERACTIVE LOGIC
   ========================================================================= */

function initAboutInteractiveFeatures() {
  // 1. Language Toggle Logic
  function updateAboutLanguage(lang) {
    const aboutPage = document.getElementById("aboutPage");
    if (!aboutPage) return;
    
    if (lang === "vi") {
      aboutPage.classList.remove("lang-selected-en");
      aboutPage.classList.add("lang-selected-vi");
      document.getElementById("aboutLangViBtn")?.classList.add("active");
      document.getElementById("aboutLangEnBtn")?.classList.remove("active");
    } else {
      aboutPage.classList.remove("lang-selected-vi");
      aboutPage.classList.add("lang-selected-en");
      document.getElementById("aboutLangEnBtn")?.classList.add("active");
      document.getElementById("aboutLangViBtn")?.classList.remove("active");
    }
    localStorage.setItem("about-lang", lang);
    
    // Re-trigger terminal typing preview with new language
    const activeTab = document.querySelector(".about-mode-tab-btn.active");
    if (activeTab) {
      triggerTerminalPreview(activeTab.getAttribute("data-mode"));
    }
  }

  document.getElementById("aboutLangEnBtn")?.addEventListener("click", () => updateAboutLanguage("en"));
  document.getElementById("aboutLangViBtn")?.addEventListener("click", () => updateAboutLanguage("vi"));

  // 2. Interactive Terminal Mock Data & Logic
  const terminalData = {
    en: {
      adventure: [
        { text: "Initializing Cosmic Engine...", type: "system" },
        { text: "World Seed: 0x8F94D2 - 'Aethelgard Void'", type: "system" },
        { text: "Loading Character: Vaelen (Stardust Rogue)...", type: "system" },
        { text: "> You stand before the shattered Obsidian Spire. The air is cold, smelling of ozone and dead magic.", type: "story" },
        { text: "[1] Venture into the Spire's glowing tear", type: "choice" },
        { text: "[2] Scan the perimeter for cosmic residual signs", type: "choice" },
        { text: "[3] Retreat to the safety of your shuttle", type: "choice" }
      ],
      novel: [
        { text: "Building Story Bible...", type: "system" },
        { text: "Registering Lore: The Iron Pact of 2084", type: "system" },
        { text: "Configuring Tone: Cyber-noir, melancholic, rich prose", type: "system" },
        { text: "> The neon rain fell like liquid silver, painting the narrow alleys of District 9 in fractured reflections. Detective Kael adjusted his collar, the hum of his cybernetic arm a faint companion in the dark. 'She was here,' he muttered to the database. 'I can still feel the heat signature.'", type: "story" },
        { text: "> Direction: Detail Kael's next move or describe the approaching footsteps?", type: "system" }
      ]
    },
    vi: {
      adventure: [
        { text: "Đang khởi tạo Động cơ Vũ trụ...", type: "system" },
        { text: "Hạt giống thế giới: 0x8F94D2 - 'Kẻ Không Hồn'", type: "system" },
        { text: "Tải nhân vật: Vaelen (Kẻ Trộm Ánh Sao)...", type: "system" },
        { text: "> Bạn đang đứng trước Tháp Hắc Diện Thạch vỡ vụn. Không khí lạnh buốt, nồng nặc mùi ozone và ma thuật đã tàn.", type: "story" },
        { text: "[1] Tiến vào vết nứt phát sáng của Tháp", type: "choice" },
        { text: "[2] Quét xung quanh tìm tàn tích năng lượng", type: "choice" },
        { text: "[3] Rút lui về phi thuyền an toàn", type: "choice" }
      ],
      novel: [
        { text: "Đang thiết lập Story Bible...", type: "system" },
        { text: "Đăng ký Truyền thuyết: Khế ước Sắt năm 2084", type: "system" },
        { text: "Định cấu hình Văn phong: U tối, điện ảnh, giàu cảm xúc", type: "system" },
        { text: "> Cơn mưa neon rơi như bạc lỏng, nhuộm những con hẻm nhỏ của Quận 9 trong những hình ảnh phản chiếu vỡ vụn. Thám tử Kael chỉnh lại cổ áo, tiếng cánh tay cơ khí kêu rì rì nhỏ trong bóng tối. 'Cô ấy đã ở đây,' anh lẩm bẩm với cơ sở dữ liệu. 'Tôi vẫn cảm nhận được nhiệt lượng.'", type: "story" },
        { text: "> Định hướng tiếp theo: Mô tả chi tiết hành động của Kael hay mô tả tiếng bước chân đang đến gần?", type: "system" }
      ]
    }
  };

  let terminalTimeout = null;
  function triggerTerminalPreview(mode) {
    const terminalBody = document.getElementById("aboutTerminalPreview");
    if (!terminalBody) return;
    
    if (terminalTimeout) {
      clearTimeout(terminalTimeout);
    }
    terminalBody.innerHTML = "";
    
    const lang = localStorage.getItem("about-lang") || "en";
    const lines = terminalData[lang][mode] || [];
    let lineIndex = 0;
    
    function typeNextLine() {
      if (lineIndex >= lines.length) {
        const cursor = document.createElement("span");
        cursor.className = "cursor-blink";
        terminalBody.appendChild(cursor);
        return;
      }
      
      const lineInfo = lines[lineIndex];
      const lineEl = document.createElement("span");
      lineEl.className = "term-line";
      
      if (lineInfo.type === "system") {
        lineEl.className += " term-system";
        lineEl.style.color = "rgba(255, 255, 255, 0.4)";
      } else if (lineInfo.type === "story") {
        lineEl.className += " term-story";
        lineEl.style.color = "var(--text)";
        lineEl.style.fontWeight = "600";
      } else if (lineInfo.type === "choice") {
        lineEl.className += " term-choice";
      }
      
      terminalBody.appendChild(lineEl);
      
      let charIndex = 0;
      const text = lineInfo.text;
      
      function typeChar() {
        if (charIndex >= text.length) {
          lineIndex++;
          terminalTimeout = setTimeout(typeNextLine, lineInfo.type === "choice" ? 120 : 350);
          return;
        }
        lineEl.textContent += text[charIndex];
        charIndex++;
        terminalTimeout = setTimeout(typeChar, 8);
      }
      
      typeChar();
    }
    
    typeNextLine();
  }

  document.querySelectorAll(".about-mode-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".about-mode-tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const mode = btn.getAttribute("data-mode");
      triggerTerminalPreview(mode);
    });
  });

  // 3. Memory Architecture Diagnostics Switcher
  const memoryDiagData = {
    summary: {
      component: "StorySummary",
      status: "COMPRESSED",
      tokens: 420,
      summary: "Player (Vaelen) entered the Spire, acquired a glowing shard, and successfully bypassed the sentinel security grid."
    },
    facts: {
      component: "ImportantFacts",
      entities: ["Vaelen", "Sentinel Grid", "Obsidian Spire"],
      inventory: ["Obsidian Shard", "Decoy Flare"],
      relations: {
        "Sentinels": "Hostile",
        "Collector": "Neutral"
      }
    },
    vector: {
      component: "VectorMemories",
      db_instance: "ChromaDB",
      collection: "session_mem_194b",
      last_query: "shattered tower rogue sentinel",
      nearest_matches: [
        { id: "msg_003", distance: 0.22, content: "Kael mentions Spire defenses are weak from the east side" },
        { id: "msg_012", distance: 0.35, content: "Obsidian spire sentinel shoots plasma flares" }
      ]
    },
    history: {
      component: "PersistentHistory",
      database: "Cloud Firestore",
      session_id: "9a2f-14bc-7c3d",
      user_id: "firebase_auth_user_uuid",
      total_turns: 45,
      last_save_time: "2026-05-22T05:37:32Z"
    }
  };

  function formatDiagnosticJSON(obj) {
    const rawJson = JSON.stringify(obj, null, 2);
    return rawJson.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
      let cls = 'diagnostics-val';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'diagnostics-key';
        } else {
          cls = 'diagnostics-str';
        }
      }
      return '<span class="' + cls + '">' + match + '</span>';
    });
  }

  function updateDiagnostics(type) {
    const codeBox = document.getElementById("aboutMemoryDiagnostics");
    const metadataTitle = document.getElementById("aboutDiagnosticsTitle");
    if (!codeBox) return;
    
    const data = memoryDiagData[type];
    if (!data) return;
    
    if (metadataTitle) {
      metadataTitle.textContent = `DIAGNOSTIC_METADATA_STREAM: ${type.toUpperCase()}_BLOCK`;
    }
    
    codeBox.innerHTML = formatDiagnosticJSON(data);
  }

  document.querySelectorAll(".about-memory-card").forEach(card => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".about-memory-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const type = card.getAttribute("data-memory");
      updateDiagnostics(type);
    });
  });

  // 4. Interactive Story Concept Playground (Forge)
  const playgroundResponses = {
    en: {
      "cosmic-horror": {
        "memory-loss": "World Seed: 'Xylos-9'. You awake inside an abandoned starship docking bay with no memory of who you are. The spaceship log lists you as deceased. Outside the glass, the stars are slowly blinking out one by one in a perfect spiral pattern. A faint heartbeat is echoing from the ship's ventilation system.",
        "faction-war": "World Seed: 'Azathoth-Grip'. The Solar Navy is engaged in an endless battle with the Cult of the Deep Void. You intercept a tactical transmission containing coordinates to a slumbering god. Both factions will hunt you down if they discover you possess this key.",
        "artifact": "World Seed: 'Gargantua-Eye'. You discover a black obsidian orb orbiting a dying pulsar. Every time you touch it, you relive the final, terrified moments of an alien civilization that perished a billion years ago. It warns of something massive coming.",
        "betrayal": "World Seed: 'Void-Covenant'. Your crewmates have signed a secret pact with an ancient cosmic entity to sacrifice you at the edge of the event horizon. You find the ritual markings on the ship's engine core just hours before arrival."
      },
      "cyber-fantasy": {
        "memory-loss": "World Seed: 'Neo-Avalon'. You are a street-level wizard in a neon-drenched metropolis with wiped memory chips. Your spell-matrix deck contains a single, forbidden soul-binding ritual. The corporate police are scanning your cybernetics for this signature.",
        "faction-war": "World Seed: 'Megacity-Spire'. The Megacorp Elites and the Underground Elven Syndicate are fighting for control of the digital Lifeline. You hold the decryption cipher that can either freeze all cybernetics in the city or unlock magic for the poor.",
        "artifact": "World Seed: 'Excalibur-Net'. While hacking a high-security server, you compile a legendary digital blade that physically crystallizes on your workbench. The weapon whispers ancient runes in your head, warning of executioners sent to reclaim it.",
        "betrayal": "World Seed: 'Chroma-Betrayal'. Your partner, a rogue AI, sold your location to the corporate syndicate. You escape into the dark web just as physical drones breach your safehouse, leaving you with only a burner deck."
      },
      "grimdark-steampunk": {
        "memory-loss": "World Seed: 'Iron-Aether'. You wake up covered in soot inside a runaway steam train with mechanical limbs you don't remember installing. A ticking pocketwatch in your pocket reads: 'Do not let the furnace go cold.'",
        "faction-war": "World Seed: 'Rust-Valleys'. The Sovereign Gear-Guilds and the rebel Coal-Scavengers are tearing the city apart. You are a mercenary who discovered a blueprints chest for a perpetual energy engine that both sides would burn the skies to own.",
        "artifact": "World Seed: 'Brass-Astrolabe'. You steal an ancient astronomical device from a clockwork vault. It doesn't track stars; instead, it predicts the exact second people around you will die. The first prediction is yours, set for midnight.",
        "betrayal": "World Seed: 'Steam-Covenant'. The airship captain who raised you has traded your life to the Guilds in exchange for a cache of pure aether fuel. You hear the gears of the brig locking while flying over the toxic mist."
      },
      "dream-surrealism": {
        "memory-loss": "World Seed: 'Solitude-Sea'. You walk on a beach where the sand is made of forgotten names, including your own. A lighthouse in the distance casts a shadow that speaks in your childhood voice, offering pieces of your past.",
        "faction-war": "World Seed: 'Clockwork-Dream'. The Lords of Daylight and the Sovereigns of the Moon are battling over a giant hourglass. You are a dreamwalker who can shift the sands, altering the memories of everyone in the realm.",
        "artifact": "World Seed: 'Mirror-Tear'. You find a mirror that doesn't reflect your face, but rather the person you could have been if you had made different choices. Reaching through the glass allows you to swap items with your alternate self.",
        "betrayal": "World Seed: 'Glass-Tower'. The shadow you cast has detached itself and begun plotting with the dream-keepers to lock you in a loop of perpetual night. You must catch your shadow before sunrise."
      }
    },
    vi: {
      "cosmic-horror": {
        "memory-loss": "Hạt giống thế giới: 'Xylos-9'. Bạn thức dậy trong khoang cập cảng của một tàu vũ trụ bị bỏ hoang, không ký ức. Nhật ký tàu ghi nhận bạn đã tử vong. Ngoài ô kính, các ngôi sao đang tắt dần từng ngôi một theo hình xoắn ốc hoàn hảo. Một nhịp tim yếu ớt đang vọng ra từ hệ thống thông gió.",
        "faction-war": "Hạt giống thế giới: 'Azathoth-Grip'. Hải quân Thái dương đang giao tranh với Giáo phái Hư vô. Bạn bắt được tín hiệu chứa tọa độ của một cổ thần đang ngủ say. Cả hai phe sẽ truy sát bạn nếu biết bạn nắm giữ chìa khóa này.",
        "artifact": "Hạt giống thế giới: 'Gargantua-Eye'. Bạn phát hiện một quả cầu đá hắc thạch bay quanh một pulsar đang lụi tàn. Mỗi khi chạm vào, bạn trải nghiệm những khoảnh khắc cuối cùng của một nền văn minh ngoài hành tinh đã diệt vong tỷ năm trước.",
        "betrayal": "Hạt giống thế giới: 'Void-Covenant'. Thủy thủ đoàn của bạn đã ký một khế ước bí mật với một thực thể cổ đại để hiến tế bạn tại rìa chân trời sự kiện. Bạn tìm thấy các ký hiệu nghi lễ trên lõi động cơ chỉ vài giờ trước khi đến nơi."
      },
      "cyber-fantasy": {
        "memory-loss": "Hạt giống thế giới: 'Neo-Avalon'. Bạn là một thuật sĩ đường phố tại một siêu đô thị ngập tràn ánh đèn neon với các chip ký ức bị xóa sạch. Thiết bị phép thuật của bạn chứa một nghi lễ cấm. Cảnh sát tập đoàn đang quét thiết bị của bạn.",
        "faction-war": "Hạt giống thế giới: 'Megacity-Spire'. Giới tinh hoa tập đoàn và Nghiệp đoàn yêu tinh đang chiến đấu giành quyền kiểm soát Lifeline kỹ thuật số. Bạn giữ mật mã giải mã có thể đóng băng tất cả thiết bị cơ khí trong thành phố.",
        "artifact": "Hạt giống thế giới: 'Excalibur-Net'. Trong khi hack máy chủ bảo mật cao, bạn biên dịch được một lưỡi kiếm kỹ thuật số huyền thoại kết tinh vật lý trên bàn làm việc. Vũ khí thì thầm cổ tự, cảnh báo sát thủ đang tới.",
        "betrayal": "Hạt giống thế giới: 'Chroma-Betrayal'. Người cộng sự AI của bạn đã bán vị trí của bạn cho tập đoàn. Bạn trốn vào thế giới web tối ngay khi drone của tập đoàn phá vỡ căn nhà an toàn."
      },
      "grimdark-steampunk": {
        "memory-loss": "Hạt giống thế giới: 'Iron-Aether'. Bạn thức dậy đầy muội than bên trong một đoàn tàu hơi nước đang lao đi mất kiểm soát với các chi cơ khí bạn không nhớ đã lắp đặt. Đồng hồ bỏ túi chạy tích tắc ghi: 'Đừng để lò nguội.'",
        "faction-war": "Hạt giống thế giới: 'Rust-Valleys'. Hiệp hội Bánh răng và Lực lượng Nhặt rác đang xé nát thành phố. Bạn phát hiện rương bản vẽ động cơ năng lượng vĩnh cửu mà cả hai bên sẵn sàng thiêu rui bầu trời để sở hữu.",
        "artifact": "Hạt giống thế giới: 'Brass-Astrolabe'. Bạn đánh cắp một thiết bị thiên văn cổ từ hầm clockwork. Nó không theo dõi sao; nó dự đoán chính xác giây phút những người xung quanh bạn sẽ chết. Dự đoán đầu tiên dành cho bạn, vào nửa đêm.",
        "betrayal": "Hạt giống thế giới: 'Steam-Covenant'. Thuyền trưởng khinh khí cầu đã đổi mạng bạn lấy một thùng nhiên liệu aether nguyên chất. Bạn nghe tiếng bánh răng khóa buồng giam khi đang bay trên màn sương độc."
      },
      "dream-surrealism": {
        "memory-loss": "Hạt giống thế giới: 'Solitude-Sea'. Bạn đi trên bãi biển nơi cát được tạo nên từ những cái tên bị lãng quên, bao gồm cả tên bạn. Một ngọn hải đăng ở phía xa phát ra giọng nói thời thơ ấu của bạn, trao lại từng mảnh ký ức.",
        "faction-war": "Hạt giống thế giới: 'Clockwork-Dream'. Chúa tể Ánh sáng và Vương chủ Ánh trăng đang tranh giành một chiếc đồng hồ cát khổng lồ. Bạn có thể dịch chuyển dòng cát, thay đổi ký ức của mọi người trong cõi mộng.",
        "artifact": "Hạt giống thế giới: 'Mirror-Tear'. Bạn tìm thấy chiếc gương phản chiếu con người khác của bạn nếu đưa ra lựa chọn khác. Chạm qua gương cho phép bạn trao đổi đồ vật với bản thể song song đó.",
        "betrayal": "Hạt giống thế giới: 'Glass-Tower'. Cái bóng của bạn đã tách ra và bắt đầu âm mưu với những người giữ mộng để nhốt bạn vào vòng lặp đêm vĩnh cửu. Bạn phải bắt bóng trước khi bình minh lên."
      }
    }
  };

  const forgeBtn = document.getElementById("aboutPlaygroundForgeBtn");
  const playgroundOutput = document.getElementById("aboutPlaygroundOutput");
  if (forgeBtn && playgroundOutput) {
    forgeBtn.addEventListener("click", () => {
      const genre = document.getElementById("aboutPlaygroundGenre").value;
      const conflict = document.getElementById("aboutPlaygroundConflict").value;
      const lang = localStorage.getItem("about-lang") || "en";
      
      const loadingMsg = lang === "vi" ? "[Đang tạo Hạt giống Thế giới...]" : "[Forging world pathways...]";
      playgroundOutput.innerHTML = `<span class="terminal-placeholder">${loadingMsg}</span>`;
      
      let dots = 0;
      const interval = setInterval(() => {
        dots = (dots + 1) % 4;
        playgroundOutput.innerHTML = `<span class="terminal-placeholder">${loadingMsg + ".".repeat(dots)}</span>`;
      }, 300);
      
      setTimeout(() => {
        clearInterval(interval);
        const result = playgroundResponses[lang][genre][conflict] || "Seed not found.";
        playgroundOutput.innerHTML = "";
        
        let charIdx = 0;
        function typeResult() {
          if (charIdx >= result.length) return;
          playgroundOutput.textContent += result[charIdx];
          charIdx++;
          setTimeout(typeResult, 12);
        }
        typeResult();
      }, 1200);
    });
  }

  // 5. FAQ Accordion Logic
  document.querySelectorAll(".faq-header").forEach(header => {
    header.addEventListener("click", () => {
      const item = header.closest(".faq-item");
      const body = item.querySelector(".faq-body");
      const isActive = item.classList.contains("active");
      
      document.querySelectorAll(".faq-item").forEach(otherItem => {
        if (otherItem !== item) {
          otherItem.classList.remove("active");
          otherItem.querySelector(".faq-body").style.maxHeight = "0";
        }
      });
      
      if (isActive) {
        item.classList.remove("active");
        body.style.maxHeight = "0";
      } else {
        item.classList.add("active");
        body.style.maxHeight = body.scrollHeight + "px";
      }
    });
  });

  // Initial runs
  const savedLang = localStorage.getItem("about-lang") || "en";
  updateAboutLanguage(savedLang);
  
  const firstCard = document.querySelector(".about-memory-card");
  if (firstCard) {
    updateDiagnostics(firstCard.getAttribute("data-memory"));
  }
}

// Call init when script loads
initLoginAnimations();
initAboutInteractiveFeatures();


/* =========================================================================
   COMMUNITY UGC & PURE NOVEL READER LOGIC
   ========================================================================= */

function normalizeCommunityWorld(world = {}) {
  return {
    id: world.id || "",
    title: world.title || "Untitled World",
    mode: world.mode || "Adventure",
    description: world.description || "",
    image: "linear-gradient(135deg, #181124, #081a2e)",
    worldSeed: world.world_seed || "",
    longDescription: world.long_description || "",
    tags: Array.isArray(world.tags) ? world.tags : [],
    isCommunity: true,
    authorName: world.author_name || "Anonymous",
    authorUid: world.author_uid || "",
    likes: world.likes || 0,
    likedBy: Array.isArray(world.liked_by) ? world.liked_by : [],
    sessionId: world.session_id || null,
  };
}

async function likeCommunityWorld(worldId, countElement) {
  try {
    const res = await requestJson(`${API_BASE}/game/discover/${encodeURIComponent(worldId)}/like`, {
      method: "POST"
    });
    if (res && countElement) {
      countElement.textContent = res.likes;
      const item = communityWorlds.find(w => w.id === worldId);
      if (item) {
        item.likes = res.likes;
      }
    }
  } catch (err) {
    console.error(err);
    alert(err.message || "Could not like this world.");
  }
}

async function deleteCommunityWorld(worldId) {
  try {
    setDiscoverStatus("Deleting publication...", "muted");
    await requestJson(`${API_BASE}/game/worlds/publish/${encodeURIComponent(worldId)}`, {
      method: "DELETE"
    });
    setDiscoverStatus("Đã xóa thế giới thành công.", "success");
    await loadWorldCatalog({ force: true });
  } catch (err) {
    console.error(err);
    alert(err.message || "Không thể xóa bài viết này.");
    setDiscoverStatus(err.message || "Error deleting publication.", "error");
  }
}

async function openStoryReaderModal(world) {
  const modal = document.getElementById("storyReaderModal");
  const authorEl = document.getElementById("storyReaderAuthor");
  const titleEl = document.getElementById("storyReaderTitle");
  const descEl = document.getElementById("storyReaderDesc");
  const contentEl = document.getElementById("storyReaderContent");
  const cloneBtn = document.getElementById("storyReaderCloneBtn");

  if (!modal) return;

  authorEl.textContent = `Legendary Story Log by ${world.authorName}`;
  titleEl.textContent = world.title;
  descEl.textContent = world.description;
  contentEl.innerHTML = "<p class='muted'>Loading story logs...</p>";

  modal.classList.remove("hidden");
  modal.classList.add("visible");

  cloneBtn.onclick = () => {
    modal.classList.remove("visible");
    modal.classList.add("hidden");
    selectCreatorWorld(world);
  };

  try {
    const res = await requestJson(`${API_BASE}/game/discover/${encodeURIComponent(world.id)}/logs`);
    if (res && Array.isArray(res.messages)) {
      contentEl.innerHTML = "";
      const storyMessages = res.messages.filter(m => m.role === "user" || m.role === "ai");
      if (storyMessages.length === 0) {
        contentEl.innerHTML = "<p class='muted'>No messages found in this story log.</p>";
      } else {
        storyMessages.forEach(msg => {
          const p = document.createElement("p");
          p.className = msg.role === "user" ? "user-message-log" : "ai-message-log";
          p.innerHTML = msg.role === "user" 
            ? `<strong>&gt; ${escapeHtml(msg.content)}</strong>` 
            : escapeHtml(msg.content).replace(/\n/g, "<br/>");
          contentEl.appendChild(p);
        });
      }
    } else {
      contentEl.innerHTML = "<p class='muted'>Could not fetch story logs.</p>";
    }
  } catch (err) {
    console.error(err);
    contentEl.innerHTML = `<p class='error-text'>Error: ${escapeHtml(err.message)}</p>`;
  }
}

function openPublishModal(sessionId, sessionTitle) {
  const modal = document.getElementById("publishWorldModal");
  const sessIdInput = document.getElementById("publishSessionId");
  const titleInput = document.getElementById("publishTitle");
  const descInput = document.getElementById("publishDescription");
  const tagsInput = document.getElementById("publishTags");

  if (!modal) return;

  sessIdInput.value = sessionId;
  titleInput.value = sessionTitle || "";
  descInput.value = "";
  tagsInput.value = "";

  modal.classList.remove("hidden");
  modal.classList.add("visible");
}

// Modal setup events
document.getElementById("closePublishModalBtn")?.addEventListener("click", () => {
  const modal = document.getElementById("publishWorldModal");
  modal.classList.remove("visible");
  modal.classList.add("hidden");
});
document.getElementById("publishModalBackdrop")?.addEventListener("click", () => {
  const modal = document.getElementById("publishWorldModal");
  modal.classList.remove("visible");
  modal.classList.add("hidden");
});

document.getElementById("publishWorldForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const sessionId = document.getElementById("publishSessionId").value;
  const title = document.getElementById("publishTitle").value;
  const description = document.getElementById("publishDescription").value;
  const tagsText = document.getElementById("publishTags").value;
  const tags = tagsText.split(",").map(t => t.trim()).filter(Boolean);

  const btn = document.getElementById("submitPublishBtn");
  const origText = btn.textContent;
  btn.textContent = "Publishing...";
  btn.disabled = true;

  try {
    const res = await requestJson(`${API_BASE}/game/worlds/publish`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, title, description, tags })
    });
    alert(res.message || "Published successfully! Awaiting admin review.");
    const modal = document.getElementById("publishWorldModal");
    modal.classList.remove("visible");
    modal.classList.add("hidden");
  } catch (err) {
    console.error(err);
    alert(err.message || "Failed to publish.");
  } finally {
    btn.textContent = origText;
    btn.disabled = false;
  }
});

document.getElementById("closeStoryReaderModalBtn")?.addEventListener("click", () => {
  const modal = document.getElementById("storyReaderModal");
  modal.classList.remove("visible");
  modal.classList.add("hidden");
});
document.getElementById("readerModalBackdrop")?.addEventListener("click", () => {
  const modal = document.getElementById("storyReaderModal");
  modal.classList.remove("visible");
  modal.classList.add("hidden");
});

// Pure Novel Read Mode Toggle Logic
const pureReadModeBtn = document.getElementById("pureReadModeBtn");
pureReadModeBtn?.addEventListener("click", () => {
  const gamePage = document.getElementById("gamePage");
  if (!gamePage) return;

  const isActive = gamePage.classList.toggle("pure-read-active");
  pureReadModeBtn.classList.toggle("active", isActive);

  if (isActive) {
    pureReadModeBtn.innerHTML = "Play";
    const composerStatus = document.getElementById("composerStatus");
    if (composerStatus) composerStatus.textContent = "Pure reading mode activated.";
  } else {
    pureReadModeBtn.innerHTML = "Read";
    const composerStatus = document.getElementById("composerStatus");
    if (composerStatus) composerStatus.textContent = "Interactive mode activated.";
  }
});

// Wire up global search input to act as filter redirect
globalSearchInput?.addEventListener("input", () => {
  const query = globalSearchInput.value;
  
  if (savesPage && !savesPage.classList.contains("hidden")) {
    if (saveSearchInput) {
      saveSearchInput.value = query;
      renderSavedSessions();
    }
  } else {
    if (discoverPage && discoverPage.classList.contains("hidden")) {
      showPage(discoverPage);
      const discoverNavBtn = document.getElementById("mobileDiscoverBtn") || document.getElementById("discoverBtn");
      if (discoverNavBtn) setActiveNav(discoverNavBtn);
    }
    if (discoverSearchInput) {
      discoverSearchInput.value = query;
      renderDiscoverWorlds();
    }
  }
});

globalSearchInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    closeGlobalSearch();
  }
});

// ── Theme Selector Logic ──────────────────────────────────────────────────────
const readerThemes = ["cosmic", "amoled", "sepia", "forest"];
readerThemes.forEach(theme => {
  const btn = document.getElementById(`theme${theme.charAt(0).toUpperCase() + theme.slice(1)}`);
  btn?.addEventListener("click", () => {
    document.querySelectorAll(".theme-swatch").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    if (theme === "cosmic") {
      document.body.removeAttribute("data-theme");
      localStorage.setItem("user-theme", "cosmic");
    } else {
      document.body.setAttribute("data-theme", theme);
      localStorage.setItem("user-theme", theme);
    }
  });
});

// Restore saved theme on startup
const savedTheme = localStorage.getItem("user-theme") || "cosmic";
if (savedTheme !== "cosmic" && readerThemes.includes(savedTheme)) {
  document.body.setAttribute("data-theme", savedTheme);
}
document.querySelectorAll(".theme-swatch").forEach(s => s.classList.remove("active"));
const activeThemeBtn = document.getElementById(`theme${savedTheme.charAt(0).toUpperCase() + savedTheme.slice(1)}`);
if (activeThemeBtn) {
  activeThemeBtn.classList.add("active");
}

// ── Keyboard Shortcuts (Focus, Read, Choices, Submit) ─────────────────────────
window.addEventListener("keydown", (e) => {
  const activeEl = document.activeElement;
  if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA" || activeEl.isContentEditable)) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      const sendBtn = document.getElementById("storyComposerSendBtn");
      if (sendBtn && !sendBtn.disabled) {
        e.preventDefault();
        sendBtn.click();
      }
    }
    return;
  }

  // Choose options 1, 2, 3, 4
  if (["1", "2", "3", "4"].includes(e.key)) {
    const choices = document.querySelectorAll(".choices-box button");
    const index = parseInt(e.key) - 1;
    if (choices && choices[index]) {
      e.preventDefault();
      choices[index].click();
    }
  }

  // Toggle Focus Mode (F key)
  if (e.key.toLowerCase() === "f") {
    const focusBtn = document.getElementById("readerFocusToggle");
    if (focusBtn) {
      e.preventDefault();
      focusBtn.click();
    }
  }

  // Toggle Read Mode (R key)
  if (e.key.toLowerCase() === "r") {
    const readBtn = document.getElementById("pureReadModeBtn");
    if (readBtn) {
      e.preventDefault();
      readBtn.click();
    }
  }
});

