// -- lib/walt2_splash_screen.dart
import 'package:flutter/material.dart';
import 'walt2_home_screen.dart';
import 'api_service.dart'; // Import ApiService

class Walt2SplashScreen extends StatefulWidget {
  final ApiService apiService; // Receive ApiService from main.dart

  const Walt2SplashScreen({super.key, required this.apiService}); // Constructor to receive ApiService

  @override
  _Walt2SplashScreenState createState() => _Walt2SplashScreenState();
}

class _Walt2SplashScreenState extends State<Walt2SplashScreen> {
  // String baseUrl = "https://virtual-lab-staging-jeff-b43cbb10d55f.herokuapp.com"; // No need for baseUrl here
  // late ApiService _apiService; // No need to create ApiService here, using the passed one
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // _apiService = ApiService(baseUrl: baseUrl); // No need to initialize here
    _fetchInitialData();
  }

  // @override // No need to dispose here, ApiService is managed in main.dart
  // void dispose() {
  //   _apiService.closeClient();
  //   super.dispose();
  // }

  ApiService get _apiService => widget.apiService; // Helper to access ApiService easily

  Future<void> _fetchInitialData() async {
    setState(() {
      _isLoading = true;
    });
    try {
      await _apiService.fetchCsrfToken();
      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      print("Error fetching initial data (CSRF): $e");
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error initializing app: $e")),
      );
    }
  }


  void _beginNewBio() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final initialMessage = await _apiService.getNewBioInitialMessage();
      setState(() {
        _isLoading = false;
      });
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => Walt2HomeScreen(
            initialMessage: initialMessage,
            apiService: _apiService, // Pass the SAME ApiService instance
          ),
        ),
      );
    } catch (e) {
      print("Error in _beginNewBio: $e");
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error starting new bio: $e")),
      );
    }
  }

  void _loadStory() {
    setState(() {
      _isLoading = false;
    });
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => Walt2HomeScreen(
          initialMessage: "Loading your story...",
          apiService: _apiService, // Pass the SAME ApiService instance
          loadStoryOnInit: true,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          Center(
            child: Container(
              width: MediaQuery.of(context).size.width * 0.8,
              height: MediaQuery.of(context).size.height * 0.7,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(15),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.08),
                    blurRadius: 16,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(30),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            "Walt, Your AI Biographer",
                            style: TextStyle(
                              color: Color(0xFF007AFF),
                              fontSize: 32,
                              fontWeight: FontWeight.w600,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 20),
                          const Text(
                            "I want to write your unique story!",
                            style: TextStyle(
                              color: Color(0xFF555555),
                              fontSize: 18,
                              fontStyle: FontStyle.italic,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  ),
                  Expanded(
                    child: Container(
                      color: const Color(0xFFF0F0F0),
                      padding: const EdgeInsets.all(30),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            "Get Started",
                            style: TextStyle(
                              color: Color(0xFF777777),
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 15),
                          ElevatedButton(
                            onPressed: _beginNewBio,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF007AFF),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            child: const Text("Begin New Bio"),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton(
                            onPressed: _loadStory,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF007AFF),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            child: const Text("Load Your Story"),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_isLoading)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: const Center(
                  child: CircularProgressIndicator(color: Colors.white),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
// -- lib/walt2_splash_screen.dart
